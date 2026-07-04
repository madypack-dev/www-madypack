"""Modelos Pydantic para la carga y validación de archivos YAML por tenant."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------- analytics ----------
class AnalyticsConfig(BaseModel):
    gtm_id: str
    ga_id: str


# ---------- whatsapp ----------
class WhatsAppConfig(BaseModel):
    phone: str
    message: str


# ---------- site ----------
class LogoConfig(BaseModel):
    width: int
    height: int
    alt: str
    url: str


class SiteMetadataConfig(BaseModel):
    lang: str
    brand: str
    tagline: str
    title_default: str
    charset: str
    viewport: str
    robots: str
    profile_url: str
    logo: LogoConfig


# ---------- socials ----------
class SocialConfig(BaseModel):
    network: str
    url: str | None = None
    label: str
    cta_class: str | None = None


# ---------- header ----------
class TopBarConfig(BaseModel):
    text: str


class HeaderLogoConfig(BaseModel):
    src: str


class MenuItemConfig(BaseModel):
    label: str
    url: str
    rel: str | None = None


class HeaderActionsConfig(BaseModel):
    search: str
    account: str
    cart: str
    menu: str


class AccountModalConfig(BaseModel):
    title: str
    close_label: str
    email_label: str
    email_placeholder: str
    password_label: str
    password_placeholder: str
    submit_button: str
    no_account_text: str
    contact_link_text: str
    contact_url: str


class HeaderConfig(BaseModel):
    top_bar: TopBarConfig
    logo: HeaderLogoConfig
    menu: list[MenuItemConfig]
    actions: HeaderActionsConfig
    account_modal: AccountModalConfig


# ---------- footer ----------
class FooterLogoConfig(BaseModel):
    src: str


class FooterConfig(BaseModel):
    logo: FooterLogoConfig
    menu: list[MenuItemConfig]


# ---------- home.hero ----------
class HeroConfig(BaseModel):
    title: str
    subtitle: str


# ---------- home.cta ----------
class CtaConfig(BaseModel):
    title: str
    before_link: str
    link_text: str
    after_link: str


# ---------- home.product_types ----------
class ProductTypeConfig(BaseModel):
    label: str
    image: str


class ProductTypesConfig(BaseModel):
    title: str
    products: list[ProductTypeConfig]


# ---------- home.quote_form ----------
class QuoteFormDetailConfig(BaseModel):
    title: str
    text: str


class QuoteFormFieldConfig(BaseModel):
    name: str
    label: str
    type: str
    required: bool
    rows: int | None = None
    full_width: bool | None = None


class QuoteFormConfig(BaseModel):
    title: str
    meta_title: str
    meta_description: str
    description: str
    submit: str
    success_title: str
    success_message: str
    required_marker: str
    required_abbreviation: str
    details: list[QuoteFormDetailConfig]
    fields: list[QuoteFormFieldConfig]


# ---------- home.about ----------
class AboutDetailConfig(BaseModel):
    title: str
    text: str


class AboutConfig(BaseModel):
    title: str
    meta_title: str
    meta_description: str
    text: str
    button_text: str
    button_url: str
    image: str
    details: list[AboutDetailConfig]


# ---------- home.newsletter ----------
class NewsletterConfig(BaseModel):
    title: str
    placeholder: str
    submit: str
    success_title: str
    success_message: str


# ---------- home.contact ----------
class ContactLabelsConfig(BaseModel):
    customer_service: str
    whatsapp: str
    location: str


class ContactDetailConfig(BaseModel):
    title: str
    text: str


class ContactConfig(BaseModel):
    title: str
    meta_title: str
    meta_description: str
    email: str
    whatsapp_label: str
    address: str
    map_url: str
    map_link: str
    map_title: str
    labels: ContactLabelsConfig
    details: list[ContactDetailConfig]


class HomeConfig(BaseModel):
    hero: HeroConfig
    cta: CtaConfig
    product_types: ProductTypesConfig
    quote_form: QuoteFormConfig
    about: AboutConfig
    newsletter: NewsletterConfig
    contact: ContactConfig


# ---------- cart ----------
class CartItemConfig(BaseModel):
    name: str
    description: str
    quantity_label: str
    image: str


class CartSummaryConfig(BaseModel):
    heading: str
    total_label: str
    total_value: str
    estimated_cost_label: str
    estimated_cost_value: str
    note: str
    submit_button: str


class CartConfig(BaseModel):
    title: str
    meta_description: str
    heading: str
    items_heading: str
    pending_quote_label: str
    items: list[CartItemConfig]
    summary: CartSummaryConfig


# ---------- schema ----------
class SchemaAddressConfig(BaseModel):
    streetAddress: str
    addressLocality: str
    addressRegion: str
    postalCode: str
    addressCountry: str


class SchemaGeoConfig(BaseModel):
    latitude: str
    longitude: str


class SchemaOpeningHoursConfig(BaseModel):
    days: list[str]
    opens: str
    closes: str


class SchemaConfig(BaseModel):
    type: str
    name: str
    image: str
    logo: str
    url: str
    telephone: str
    email: str
    description: str
    address: SchemaAddressConfig
    geo: SchemaGeoConfig
    opening_hours: SchemaOpeningHoursConfig


# ---------- site.yml completo ----------
class SiteConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    analytics: AnalyticsConfig
    whatsapp: WhatsAppConfig
    site: SiteMetadataConfig
    socials: list[SocialConfig]
    header: HeaderConfig
    footer: FooterConfig
    home: HomeConfig
    cart: CartConfig
    schema_config: SchemaConfig = Field(alias="schema")


# ---------- productos_tienda.yml ----------
class ArticuloCatalogo(BaseModel):
    id: int
    nombre: str
    descripcion: str
    cantidad_por_defecto: int = Field(..., ge=100)
    imagen: str

    @field_validator("cantidad_por_defecto")
    @classmethod
    def validar_multiplo_de_100(cls, valor: int) -> int:
        if valor % 100 != 0:
            raise ValueError("La cantidad por defecto debe ser múltiplo de 100.")
        return valor


class CatalogoConfig(BaseModel):
    articulos: list[ArticuloCatalogo]
