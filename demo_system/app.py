"""FastAPI Acme Commerce target exposing REST, GraphQL, DB and outbox behaviour."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import asc, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from demo_system.auth import (
    Principal,
    authenticated,
    parse_token,
    require_owner_or_role,
    require_role,
)
from demo_system.database import (
    CustomerRecord,
    Database,
    EventRecord,
    OrderRecord,
    ProductRecord,
)
from demo_system.graphql_api import execute_graphql
from demo_system.payment import DeterministicPaymentGateway, HttpPaymentGateway, PaymentGateway
from demo_system.problems import (
    ProblemError,
    problem_handler,
    problem_response,
    validation_handler,
)
from demo_system.services import (
    confirm_order_record,
    create_order_record,
    customer_payload,
    event_payload,
    now,
    order_payload,
    product_payload,
)
from framework.models.customer import CreateCustomerRequest, UpdateCustomerRequest
from framework.models.order import CreateOrderRequest
from framework.models.product import CreateProductRequest
from framework.utils.logger import configure_logging


class TokenRequest(BaseModel):
    username: str
    password: str


class GraphQLRequest(BaseModel):
    query: str
    variables: dict[str, Any] = {}
    operationName: str | None = None


def create_app(
    *,
    database_url: str | None = None,
    payment_gateway: PaymentGateway | None = None,
) -> FastAPI:
    resolved_database_url = (
        database_url or os.getenv("DATABASE_URL") or "sqlite:///./acme-commerce.db"
    )
    database = Database(resolved_database_url)
    wiremock_url = os.getenv("WIREMOCK_URL")
    gateway = payment_gateway or (
        HttpPaymentGateway(wiremock_url) if wiremock_url else DeterministicPaymentGateway()
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        database.create()
        yield
        database.dispose()

    app = FastAPI(
        title="Acme Commerce API",
        version="1.0.0",
        description="Stable target for enterprise API and integration quality engineering",
        lifespan=lifespan,
    )
    app.state.database = database
    app.state.payment_gateway = gateway
    app.add_exception_handler(ProblemError, problem_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_handler)  # type: ignore[arg-type]
    configure_logging(os.getenv("LOG_LEVEL", "INFO"))

    @app.middleware("http")
    async def correlation_middleware(request: Request, call_next: Any) -> Any:
        supplied = request.headers.get("X-Correlation-ID")
        try:
            request.state.correlation_id = str(UUID(supplied)) if supplied else str(uuid4())
        except ValueError:
            request.state.correlation_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        return response

    def get_session(request: Request) -> Iterator[Session]:
        with request.app.state.database.session() as session:
            yield session

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "UP", "service": "acme-commerce-api", "version": "1.0.0"}

    @app.post("/auth/token", tags=["identity"])
    def issue_token(request: TokenRequest) -> dict[str, Any]:
        known = {
            "admin": ("admin-demo", "admin-token", "ADMIN"),
            "support": ("support-demo", "support-token", "SUPPORT"),
        }
        expected = known.get(request.username)
        if expected is None or request.password != expected[0]:
            raise ProblemError(401, "INVALID_CREDENTIALS", "Username or password is incorrect")
        return {
            "access_token": expected[1],
            "token_type": "bearer",
            "expires_in": 3600,
            "role": expected[2],
        }

    @app.post("/customers", status_code=201, tags=["customers"])
    def create_customer(
        request: CreateCustomerRequest,
        principal: Principal = Depends(authenticated),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        require_role(principal, "ADMIN", "SUPPORT")
        customer = CustomerRecord(
            id=str(uuid4()),
            first_name=request.first_name,
            last_name=request.last_name,
            email=str(request.email).lower(),
            status="ACTIVE",
            created_at=now(),
        )
        session.add(customer)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ProblemError(
                409,
                "DUPLICATE_CUSTOMER",
                "A customer with this email already exists",
                field="email",
            ) from exc
        return customer_payload(customer)

    @app.get("/customers/{customer_id}", tags=["customers"])
    def get_customer(
        customer_id: str,
        principal: Principal = Depends(authenticated),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        customer = session.get(CustomerRecord, customer_id)
        if customer is None:
            raise ProblemError(404, "CUSTOMER_NOT_FOUND", "The customer does not exist")
        require_owner_or_role(principal, customer.id, "ADMIN", "SUPPORT")
        return customer_payload(customer)

    @app.patch("/customers/{customer_id}", tags=["customers"])
    def update_customer(
        customer_id: str,
        request: UpdateCustomerRequest,
        principal: Principal = Depends(authenticated),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        customer = session.get(CustomerRecord, customer_id)
        if customer is None:
            raise ProblemError(404, "CUSTOMER_NOT_FOUND", "The customer does not exist")
        require_owner_or_role(principal, customer.id, "ADMIN")
        if request.status is not None and principal.role != "ADMIN":
            raise ProblemError(403, "FORBIDDEN", "Only an administrator can change status")
        updates = request.model_dump(exclude_none=True)
        for key, value in updates.items():
            setattr(customer, key, value)
        session.flush()
        return customer_payload(customer)

    @app.delete("/customers/{customer_id}", status_code=204, tags=["customers"])
    def delete_customer(
        customer_id: str,
        principal: Principal = Depends(authenticated),
        session: Session = Depends(get_session),
    ) -> None:
        require_role(principal, "ADMIN")
        customer = session.get(CustomerRecord, customer_id)
        if customer is None:
            raise ProblemError(404, "CUSTOMER_NOT_FOUND", "The customer does not exist")
        session.delete(customer)

    @app.post("/products", status_code=201, tags=["products"])
    def create_product(
        request: CreateProductRequest,
        principal: Principal = Depends(authenticated),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        require_role(principal, "ADMIN")
        product = ProductRecord(
            id=str(uuid4()),
            sku=request.sku,
            name=request.name,
            price=request.price,
            inventory=request.inventory,
            created_at=now(),
        )
        session.add(product)
        try:
            session.flush()
        except IntegrityError as exc:
            raise ProblemError(
                409,
                "DUPLICATE_SKU",
                "The product SKU already exists",
                field="sku",
            ) from exc
        return product_payload(product)

    @app.get("/products/{product_id}", tags=["products"])
    def get_product(
        product_id: str,
        _principal: Principal = Depends(authenticated),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        product = session.get(ProductRecord, product_id)
        if product is None:
            raise ProblemError(404, "PRODUCT_NOT_FOUND", "The product does not exist")
        return product_payload(product)

    @app.get("/products", tags=["products"])
    def list_products(
        _principal: Principal = Depends(authenticated),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=20, ge=1, le=100),
        sort: str = Query(default="created_at", pattern="^(created_at|price|name)$"),
        direction: str = Query(default="asc", pattern="^(asc|desc)$"),
        min_inventory: int | None = Query(default=None, ge=0),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        sort_column = {
            "created_at": ProductRecord.created_at,
            "price": ProductRecord.price,
            "name": ProductRecord.name,
        }[sort]
        statement = select(ProductRecord)
        count_statement = select(func.count()).select_from(ProductRecord)
        if min_inventory is not None:
            statement = statement.where(ProductRecord.inventory >= min_inventory)
            count_statement = count_statement.where(ProductRecord.inventory >= min_inventory)
        order_by = asc(sort_column) if direction == "asc" else desc(sort_column)
        products = session.scalars(
            statement.order_by(order_by, ProductRecord.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        total = int(session.scalar(count_statement) or 0)
        return {
            "items": [product_payload(product) for product in products],
            "page": page,
            "page_size": page_size,
            "total": total,
            "sort": sort,
            "direction": direction,
        }

    @app.post("/orders", status_code=201, tags=["orders"])
    def create_order(
        request: CreateOrderRequest,
        raw_request: Request,
        principal: Principal = Depends(authenticated),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        require_owner_or_role(principal, str(request.customer_id), "ADMIN", "SUPPORT")
        order = create_order_record(session, request, raw_request.state.correlation_id)
        return order_payload(order)

    @app.get("/orders/{order_id}", tags=["orders"])
    def get_order(
        order_id: str,
        principal: Principal = Depends(authenticated),
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        order = session.get(OrderRecord, order_id)
        if order is None:
            raise ProblemError(404, "ORDER_NOT_FOUND", "The order does not exist")
        require_owner_or_role(principal, order.customer_id, "ADMIN", "SUPPORT")
        return order_payload(order)

    @app.post("/orders/{order_id}/confirm", tags=["orders", "payments"])
    def confirm_order(
        order_id: str,
        raw_request: Request,
        principal: Principal = Depends(authenticated),
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        payment_scenario: str = Header(default="approved", alias="X-Payment-Scenario"),
        session: Session = Depends(get_session),
    ) -> JSONResponse:
        order = session.get(OrderRecord, order_id)
        if order is None:
            raise ProblemError(404, "ORDER_NOT_FOUND", "The order does not exist")
        require_owner_or_role(principal, order.customer_id, "ADMIN")
        key = idempotency_key or f"order-{order.id}"
        if len(key) > 100:
            raise ProblemError(
                400,
                "VALIDATION_ERROR",
                "Idempotency key is too long",
                field="Idempotency-Key",
            )
        updated, payment, replay = confirm_order_record(
            session,
            order=order,
            gateway=raw_request.app.state.payment_gateway,
            scenario=payment_scenario,
            idempotency_key=key,
        )
        response = JSONResponse(
            status_code=200 if updated.status == "CONFIRMED" else 502,
            content={
                "order": {
                    **order_payload(updated),
                    "created_at": updated.created_at.isoformat(),
                },
                "payment": {
                    "id": payment.id,
                    "order_id": payment.order_id,
                    "status": payment.status,
                    "attempts": payment.attempts,
                    "idempotency_key": payment.idempotency_key,
                },
            },
        )
        if replay:
            response.headers["X-Idempotent-Replay"] = "true"
        return response

    @app.get("/events", tags=["events"])
    def list_events(
        _principal: Principal = Depends(authenticated),
        aggregate_id: str | None = None,
        event_type: str | None = None,
        session: Session = Depends(get_session),
    ) -> dict[str, Any]:
        statement = select(EventRecord).order_by(EventRecord.timestamp, EventRecord.sequence)
        if aggregate_id:
            statement = statement.where(EventRecord.aggregate_id == aggregate_id)
        if event_type:
            statement = statement.where(EventRecord.event_type == event_type)
        events = session.scalars(statement).all()
        return {
            "items": [
                {
                    **event_payload(event),
                    "timestamp": event.timestamp.isoformat(),
                }
                for event in events
            ],
            "total": len(events),
        }

    @app.post("/graphql", tags=["graphql"])
    async def graphql_endpoint(
        body: GraphQLRequest,
        raw_request: Request,
        authorization: str | None = Header(default=None),
        session: Session = Depends(get_session),
    ) -> JSONResponse:
        principal: Principal | None = None
        if authorization:
            scheme, _, token = authorization.partition(" ")
            if scheme.lower() == "bearer" and token:
                try:
                    principal = parse_token(token)
                except ProblemError:
                    principal = None
        payload = await execute_graphql(
            body.query,
            variables=body.variables,
            operation_name=body.operationName,
            context={
                "session": session,
                "principal": principal,
                "correlation_id": raw_request.state.correlation_id,
            },
        )
        return JSONResponse(status_code=200, content=payload)

    @app.exception_handler(404)
    async def not_found(request: Request, _exc: Exception) -> JSONResponse:
        return problem_response(
            request,
            status=404,
            code="ROUTE_NOT_FOUND",
            message="The requested route does not exist",
        )

    return app
