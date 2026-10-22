from __future__ import annotations
from datetime import datetime
from typing import Any
from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations
from .client import BackendClient


def register_tools(mcp: FastMCP, api: BackendClient) -> None:
    read_only_open_world = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
    read_only_closed_world = ToolAnnotations(readOnlyHint=True, openWorldHint=False)
    additive_external_write = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    )
    destructive_external_write = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    )

    @mcp.tool(
        description="Read append-only domain change history for the authenticated customer. Omit domain for portfolio history. Requires audit:read. Results are newest recorded first; pass next_cursor with the same filters for another page. Times must include a timezone. Requested, state_changed, and outcome events share an operation_id. Accepted is not proof of provider completion. History starts when domain auditing was enabled; agent labels are self-reported.",
        annotations=read_only_closed_world,
    )
    async def get_domain_audit_log(
        ctx: Context,
        domain: str | None = None,
        action: str | None = None,
        from_timestamp: datetime | None = None,
        to_timestamp: datetime | None = None,
        cursor: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        return await api.call(
            "get_domain_audit_log",
            ctx,
            {
                "domain": domain,
                "action": action,
                "from_timestamp": from_timestamp,
                "to_timestamp": to_timestamp,
                "cursor": cursor,
                "limit": limit,
            },
        )

    @mcp.tool(
        description="Return the authenticated AIvikings customer for the current bearer API key, including name and email when the key belongs to a customer.",
        annotations=read_only_closed_world,
    )
    async def get_current_user(ctx: Context) -> dict[str, Any]:
        return await api.call("get_current_user", ctx, {})

    availability_status_help = 'Each result has a status: available (confirmed by the registry, with price and is_premium), likely_available (no registration found by fast checks, NOT confirmed and has no price), taken, reserved, pending_delete, invalid, unsupported_tld, or unknown (see reason). Never tell the user a likely_available name is available or quote a price for it: confirm it first with depth="confirm". '

    @mcp.tool(
        description='Check availability for up to 200 domain names through AIvikings. depth="fast" answers in about a second without contacting the registry, for brainstorming many names; depth="confirm" (default) asks the registry about every name that might be free and returns prices. A good flow: check many names with depth="fast", then confirm the shortlist with depth="confirm". '
        + availability_status_help
        + "domain_type only classifies name length. Use get_domain_pricing for full price schedules.",
        annotations=read_only_open_world,
    )
    async def check_domain_availability(
        ctx: Context, domains: list[str], currency: str = "USD", depth: str = "confirm"
    ) -> dict[str, Any]:
        return await api.call(
            "check_domain_availability",
            ctx,
            {"domains": domains, "currency": currency, "depth": depth},
        )

    @mcp.tool(
        description='Check availability for one domain through AIvikings. depth="confirm" (default) asks the registry and returns the price; depth="fast" answers quickly without a price. '
        + availability_status_help
        + "domain_type only classifies name length. Use get_domain_pricing for the full price schedule.",
        annotations=read_only_open_world,
    )
    async def check_single_domain_availability(
        ctx: Context, domain: str, currency: str = "USD", depth: str = "confirm"
    ) -> dict[str, Any]:
        return await api.call(
            "check_single_domain_availability",
            ctx,
            {"domain": domain, "currency": currency, "depth": depth},
        )

    @mcp.tool(
        description="Get a fresh price quote for one domain. Returns customer-facing registration, renewal, and transfer prices, plus is_premium so the user can be told when premium pricing applies. Omit currency to use the returned currency; USD and EUR can be requested explicitly. Prices are not converted: if the requested currency is unavailable, price fields are null with a price_unavailable_reason. Never exposes upstream cost prices.",
        annotations=read_only_open_world,
    )
    async def get_domain_pricing(
        ctx: Context, domain: str, currency: str | None = None
    ) -> dict[str, Any]:
        return await api.call(
            "get_domain_pricing", ctx, {"domain": domain, "currency": currency}
        )

    @mcp.tool(
        description="Return the authenticated customer's prepaid balance for domain purchases. Returns both USD and EUR wallet balances. When automatic currency conversion is enabled, a zero balance in the requested currency does not block registration if the other wallet has enough credit; register_domain converts only the missing amount automatically.",
        annotations=read_only_closed_world,
    )
    async def get_prepaid_balance(
        ctx: Context, currency: str = "USD"
    ) -> dict[str, Any]:
        return await api.call("get_prepaid_balance", ctx, {"currency": currency})

    @mcp.tool(
        description="List exact registrar country names and IDs for creating or updating contacts.",
        annotations=read_only_closed_world,
    )
    async def list_contact_countries(ctx: Context) -> list[dict]:
        return await api.call("list_contact_countries", ctx, {})

    @mcp.tool(
        description="List exact registrar state names for a country name, country ID, or ISO code. Use the returned name in contact requests.",
        annotations=read_only_closed_world,
    )
    async def list_contact_states(ctx: Context, country: str) -> list[dict]:
        return await api.call("list_contact_states", ctx, {"country": country})

    @mcp.tool(
        description="Create a reusable contact for domain registration. Use list_contact_countries and list_contact_states to choose valid country and state names. The returned handle can be passed to register_domain and reused for multiple domains. When handle is omitted, it is generated from the company initials (or contact-name initials), four digits, and the country code.",
        annotations=additive_external_write,
    )
    async def create_contact(
        ctx: Context,
        name: str,
        email: str,
        address: str,
        city: str,
        state: str,
        country: str,
        postal_code: str,
        phone_country_code: str,
        phone_number: str,
        handle: str | None = None,
        organization: str | None = None,
        address_line_2: str | None = None,
        default_registrant: bool = False,
        default_admin: bool = False,
        default_technical: bool = False,
        default_billing: bool = False,
    ) -> dict[str, Any]:
        return await api.call(
            "create_contact",
            ctx,
            {
                "name": name,
                "email": email,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "postal_code": postal_code,
                "phone_country_code": phone_country_code,
                "phone_number": phone_number,
                "handle": handle,
                "organization": organization,
                "address_line_2": address_line_2,
                "default_registrant": default_registrant,
                "default_admin": default_admin,
                "default_technical": default_technical,
                "default_billing": default_billing,
            },
        )

    @mcp.tool(
        description="Get one reusable contact by its handle.",
        annotations=read_only_closed_world,
    )
    async def get_contact(ctx: Context, contact_handle: str) -> dict[str, Any]:
        return await api.call("get_contact", ctx, {"contact_handle": contact_handle})

    @mcp.tool(
        description="List reusable contacts belonging to the authenticated customer.",
        annotations=read_only_closed_world,
    )
    async def list_contacts(ctx: Context) -> list[dict[str, Any]]:
        return await api.call("list_contacts", ctx, {})

    @mcp.tool(
        description="List the authenticated customer's registrant/contact handles for domain registrations. Returns whether each contact is complete enough for registration, its missing required fields, its default domain-contact roles, and the handle to pass to register_domain. Always call this before attempting a domain registration.",
        annotations=read_only_closed_world,
    )
    async def list_domain_registration_contacts(ctx: Context) -> dict[str, Any]:
        return await api.call("list_domain_registration_contacts", ctx, {})

    @mcp.tool(
        description="Assign one existing contact handle as the default for selected domain-registration roles. Set assign_registrant, assign_admin, assign_technical, and/or assign_billing to true; false leaves that role unchanged. Assigning a role replaces any previous default for that role. Use this when registration validation reports a missing registrant, admin, technical, or billing contact.",
        annotations=additive_external_write,
    )
    async def assign_domain_registration_contact_roles(
        ctx: Context,
        contact_handle: str,
        assign_registrant: bool = False,
        assign_admin: bool = False,
        assign_technical: bool = False,
        assign_billing: bool = False,
    ) -> dict[str, Any]:
        return await api.call(
            "assign_domain_registration_contact_roles",
            ctx,
            {
                "contact_handle": contact_handle,
                "assign_registrant": assign_registrant,
                "assign_admin": assign_admin,
                "assign_technical": assign_technical,
                "assign_billing": assign_billing,
            },
        )

    @mcp.tool(
        description="Remove selected default domain-registration roles from one existing contact handle. Set remove_registrant, remove_admin, remove_technical, and/or remove_billing to true; false leaves that role unchanged. This does not delete the contact. Removing a role without assigning it to another contact can make registration validation fail unless register_domain is called with an explicit registration-ready contact_handle.",
        annotations=destructive_external_write,
    )
    async def remove_domain_registration_contact_roles(
        ctx: Context,
        contact_handle: str,
        remove_registrant: bool = False,
        remove_admin: bool = False,
        remove_technical: bool = False,
        remove_billing: bool = False,
    ) -> dict[str, Any]:
        return await api.call(
            "remove_domain_registration_contact_roles",
            ctx,
            {
                "contact_handle": contact_handle,
                "remove_registrant": remove_registrant,
                "remove_admin": remove_admin,
                "remove_technical": remove_technical,
                "remove_billing": remove_billing,
            },
        )

    @mcp.tool(
        description="Register a domain through AIvikings using the authenticated account's configurable default nameservers when nameservers are omitted. Call list_domain_registration_contacts first and pass contact_handle to use one complete reusable contact for registrant, admin, technical, and billing roles. If there is no registration-ready contact, call create_contact before registration. Set currency to the same USD or EUR currency used for the price quote; otherwise the customer's preferred currency is used. If that wallet is short and automatic conversion is enabled, only the missing amount is converted from the other supported wallet. For a premium domain, first show the current get_domain_pricing quote to the user and set allow_premium=true only after the user explicitly accepts that price.",
        annotations=additive_external_write,
    )
    async def register_domain(
        ctx: Context,
        domain: str,
        period_years: int,
        nameservers: list[str] | None = None,
        currency: str | None = None,
        contact_handle: str | None = None,
        allow_premium: bool = False,
    ) -> dict[str, Any]:
        return await api.call(
            "register_domain",
            ctx,
            {
                "domain": domain,
                "period_years": period_years,
                "nameservers": nameservers,
                "currency": currency,
                "contact_handle": contact_handle,
                "allow_premium": allow_premium,
            },
        )

    @mcp.tool(
        description="Fetch the latest domain status, expiry and nameservers from the registrar and refresh the saved AIvikings record. Use this for an on-demand update, including pending transfers.",
        annotations=read_only_open_world,
    )
    async def get_domain_status(ctx: Context, domain: str) -> dict[str, Any]:
        return await api.call("get_domain_status", ctx, {"domain": domain})

    @mcp.tool(
        description="List domains recorded in the local registrar datastore.",
        annotations=read_only_closed_world,
    )
    async def list_domains(ctx: Context) -> dict[str, Any]:
        return await api.call("list_domains", ctx, {})

    @mcp.tool(
        description="Renew a domain through AIvikings.",
        annotations=additive_external_write,
    )
    async def renew_domain(
        ctx: Context, domain: str, period_years: int
    ) -> dict[str, Any]:
        return await api.call(
            "renew_domain", ctx, {"domain": domain, "period_years": period_years}
        )

    @mcp.tool(
        description="Update the registrant contact for a domain owned by the authenticated customer. Pass contact_handle by itself to apply an existing reusable contact without copying its fields into a new contact record. Name, organization, or email changes require acknowledge_transfer_lock=true because they initiate registrant verification and can impose a 60-day inter-registrar transfer lock. A provider-accepted change is reported as verification pending until the registrant completes that step.",
        annotations=destructive_external_write,
    )
    async def update_registrant_contact(
        ctx: Context,
        domain: str,
        contact_handle: str | None = None,
        name: str | None = None,
        organization: str | None = None,
        email: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        country: str | None = None,
        postal_code: str | None = None,
        phone_country_code: str | None = None,
        phone_number: str | None = None,
        acknowledge_transfer_lock: bool = False,
    ) -> dict[str, Any]:
        return await api.call(
            "update_registrant_contact",
            ctx,
            {
                "domain": domain,
                "contact_handle": contact_handle,
                "name": name,
                "organization": organization,
                "email": email,
                "address": address,
                "city": city,
                "state": state,
                "country": country,
                "postal_code": postal_code,
                "phone_country_code": phone_country_code,
                "phone_number": phone_number,
                "acknowledge_transfer_lock": acknowledge_transfer_lock,
            },
        )

    @mcp.tool(
        description="Replace a domain's nameservers through AIvikings.",
        annotations=destructive_external_write,
    )
    async def update_nameservers(
        ctx: Context, domain: str, nameservers: list[str]
    ) -> dict[str, Any]:
        return await api.call(
            "update_nameservers", ctx, {"domain": domain, "nameservers": nameservers}
        )

    @mcp.tool(
        description="Configure an A record for a domain through AIvikings. Use record_name=@ or omit it for the root/apex record. To create a subdomain, pass a relative name such as www for www.example.com or staging.api for staging.api.example.com. For compatibility, a complete hostname such as www.example.com may also be passed as domain; the server will resolve it against the authenticated customer's longest matching parent domain.",
        annotations=destructive_external_write,
    )
    async def configure_dns_record(
        ctx: Context, domain: str, record_value: str, record_name: str = "@"
    ) -> dict[str, Any]:
        return await api.call(
            "configure_dns_record",
            ctx,
            {
                "domain": domain,
                "record_value": record_value,
                "record_name": record_name,
            },
        )

    @mcp.tool(
        description="List the managed DNS records for a domain owned by the authenticated customer. Use the returned DNS zone record ID when updating or deleting a record.",
        annotations=read_only_open_world,
    )
    async def list_dns_records(ctx: Context, domain: str) -> dict[str, Any]:
        return await api.call("list_dns_records", ctx, {"domain": domain})

    @mcp.tool(
        description="Add a managed DNS record to a domain owned by the authenticated customer. Supported types are A, AAAA, CNAME, MX, TXT, NS, and SRV. Relative names are expanded below the domain, including nested names such as staging.api; use @ for the zone apex. SRV records require port and weight.",
        annotations=additive_external_write,
    )
    async def add_dns_record(
        ctx: Context,
        domain: str,
        record_name: str,
        record_type: str,
        record_value: str,
        record_ttl: int = 43200,
        record_priority: int = 0,
        record_port: int | None = None,
        record_weight: int | None = None,
    ) -> dict[str, Any]:
        return await api.call(
            "add_dns_record",
            ctx,
            {
                "domain": domain,
                "record_name": record_name,
                "record_type": record_type,
                "record_value": record_value,
                "record_ttl": record_ttl,
                "record_priority": record_priority,
                "record_port": record_port,
                "record_weight": record_weight,
            },
        )

    @mcp.tool(
        description="Replace an existing managed DNS record. Call list_dns_records first and pass its DNS zone record ID. All record fields must describe the desired replacement.",
        annotations=destructive_external_write,
    )
    async def update_dns_record(
        ctx: Context,
        domain: str,
        dns_zone_record_id: str,
        record_name: str,
        record_type: str,
        record_value: str,
        record_ttl: int = 43200,
        record_priority: int = 0,
        record_port: int | None = None,
        record_weight: int | None = None,
    ) -> dict[str, Any]:
        return await api.call(
            "update_dns_record",
            ctx,
            {
                "domain": domain,
                "dns_zone_record_id": dns_zone_record_id,
                "record_name": record_name,
                "record_type": record_type,
                "record_value": record_value,
                "record_ttl": record_ttl,
                "record_priority": record_priority,
                "record_port": record_port,
                "record_weight": record_weight,
            },
        )

    @mcp.tool(
        description="Permanently delete a managed DNS record. Call list_dns_records first and pass the exact DNS zone record ID returned by the provider.",
        annotations=destructive_external_write,
    )
    async def delete_dns_record(
        ctx: Context, domain: str, dns_zone_record_id: str
    ) -> dict[str, Any]:
        return await api.call(
            "delete_dns_record",
            ctx,
            {"domain": domain, "dns_zone_record_id": dns_zone_record_id},
        )

    @mcp.tool(
        description="Transfer a domain in through AIvikings.",
        annotations=additive_external_write,
    )
    async def domain_transfer(
        ctx: Context, domain: str, auth_code: str, period_years: int = 1
    ) -> dict[str, Any]:
        return await api.call(
            "domain_transfer",
            ctx,
            {"domain": domain, "auth_code": auth_code, "period_years": period_years},
        )

    @mcp.tool(
        description="Return the EPP transfer auth code for a domain owned by the authenticated customer. The secret is fetched only on demand.",
        annotations=read_only_closed_world,
    )
    async def get_transfer_auth_code(ctx: Context, domain: str) -> dict[str, Any]:
        return await api.call("get_transfer_auth_code", ctx, {"domain": domain})

    @mcp.tool(
        description="Regenerate and return a new EPP transfer auth code for a domain owned by the authenticated customer, invalidating the old code.",
        annotations=destructive_external_write,
    )
    async def regenerate_transfer_auth_code(
        ctx: Context, domain: str
    ) -> dict[str, Any]:
        return await api.call("regenerate_transfer_auth_code", ctx, {"domain": domain})

    @mcp.tool(
        description="Enable the registrar transfer lock for a domain owned by the authenticated customer.",
        annotations=destructive_external_write,
    )
    async def lock_domain(ctx: Context, domain: str) -> dict[str, Any]:
        return await api.call("lock_domain", ctx, {"domain": domain})

    @mcp.tool(
        description="Disable the registrar transfer lock for a domain owned by the authenticated customer before a transfer-out.",
        annotations=destructive_external_write,
    )
    async def unlock_domain(ctx: Context, domain: str) -> dict[str, Any]:
        return await api.call("unlock_domain", ctx, {"domain": domain})

    @mcp.tool(
        description="Compare locally recorded domains with AIvikings records.",
        annotations=read_only_open_world,
    )
    async def reconcile_domains(ctx: Context) -> dict[str, Any]:
        return await api.call("reconcile_domains", ctx, {})

    @mcp.tool(
        description="Create a new customer without generating or returning an API key.",
        annotations=additive_external_write,
    )
    async def create_customer(
        ctx: Context,
        email: str,
        display_name: str | None = None,
        company_name: str | None = None,
        referral_code: str | None = None,
        referred_by: str | None = None,
        preferred_currency: str = "USD",
    ) -> dict[str, Any]:
        return await api.call(
            "create_customer",
            ctx,
            {
                "email": email,
                "display_name": display_name,
                "company_name": company_name,
                "referral_code": referral_code,
                "referred_by": referred_by,
                "preferred_currency": preferred_currency,
            },
        )

    @mcp.tool(
        description="Get the customer record linked to the current bearer token. A supplied customer ID must match that token.",
        annotations=read_only_closed_world,
    )
    async def get_customer(
        ctx: Context, customer_id: str | int | None = None
    ) -> dict[str, Any]:
        return await api.call("get_customer", ctx, {"customer_id": customer_id})

    @mcp.tool(
        description="Link or create the authenticated customer's registrar client account, preventing duplicate creation.",
        annotations=additive_external_write,
    )
    async def reconcile_provider_client(
        ctx: Context, customer_id: str | int | None = None
    ) -> dict[str, Any]:
        return await api.call(
            "reconcile_provider_client", ctx, {"customer_id": customer_id}
        )
