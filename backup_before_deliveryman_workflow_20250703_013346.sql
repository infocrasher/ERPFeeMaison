--
-- PostgreSQL database dump
--

-- Dumped from database version 14.18 (Homebrew)
-- Dumped by pg_dump version 14.18 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: purchasestatus; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.purchasestatus AS ENUM (
    'DRAFT',
    'REQUESTED',
    'APPROVED',
    'ORDERED',
    'PARTIALLY_RECEIVED',
    'RECEIVED',
    'INVOICED',
    'CANCELLED'
);


ALTER TYPE public.purchasestatus OWNER TO fee_maison_user;

--
-- Name: purchaseurgency; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.purchaseurgency AS ENUM (
    'LOW',
    'NORMAL',
    'HIGH',
    'URGENT'
);


ALTER TYPE public.purchaseurgency OWNER TO fee_maison_user;

--
-- Name: stocklocationtype; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.stocklocationtype AS ENUM (
    'COMPTOIR',
    'INGREDIENTS_LOCAL',
    'INGREDIENTS_MAGASIN',
    'CONSOMMABLES'
);


ALTER TYPE public.stocklocationtype OWNER TO fee_maison_user;

--
-- Name: stockmovementtype; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.stockmovementtype AS ENUM (
    'ENTREE',
    'SORTIE',
    'TRANSFERT_SORTIE',
    'TRANSFERT_ENTREE',
    'AJUSTEMENT_POSITIF',
    'AJUSTEMENT_NEGATIF',
    'PRODUCTION',
    'VENTE',
    'INVENTAIRE'
);


ALTER TYPE public.stockmovementtype OWNER TO fee_maison_user;

--
-- Name: transferstatus; Type: TYPE; Schema: public; Owner: fee_maison_user
--

CREATE TYPE public.transferstatus AS ENUM (
    'DRAFT',
    'REQUESTED',
    'APPROVED',
    'IN_TRANSIT',
    'COMPLETED',
    'CANCELLED'
);


ALTER TYPE public.transferstatus OWNER TO fee_maison_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO fee_maison_user;

--
-- Name: cash_movement; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.cash_movement (
    id integer NOT NULL,
    session_id integer,
    created_at timestamp without time zone,
    type character varying(32),
    amount double precision NOT NULL,
    reason character varying(128),
    employee_id integer,
    notes text
);


ALTER TABLE public.cash_movement OWNER TO fee_maison_user;

--
-- Name: cash_movement_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.cash_movement_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cash_movement_id_seq OWNER TO fee_maison_user;

--
-- Name: cash_movement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.cash_movement_id_seq OWNED BY public.cash_movement.id;


--
-- Name: cash_register_session; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.cash_register_session (
    id integer NOT NULL,
    opened_at timestamp without time zone,
    closed_at timestamp without time zone,
    initial_amount double precision NOT NULL,
    closing_amount double precision,
    opened_by_id integer,
    closed_by_id integer,
    is_open boolean
);


ALTER TABLE public.cash_register_session OWNER TO fee_maison_user;

--
-- Name: cash_register_session_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.cash_register_session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cash_register_session_id_seq OWNER TO fee_maison_user;

--
-- Name: cash_register_session_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.cash_register_session_id_seq OWNED BY public.cash_register_session.id;


--
-- Name: categories; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.categories (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    description text,
    created_at timestamp without time zone
);


ALTER TABLE public.categories OWNER TO fee_maison_user;

--
-- Name: categories_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.categories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.categories_id_seq OWNER TO fee_maison_user;

--
-- Name: categories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.categories_id_seq OWNED BY public.categories.id;


--
-- Name: delivery_debts; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.delivery_debts (
    id integer NOT NULL,
    order_id integer NOT NULL,
    deliveryman_id integer NOT NULL,
    amount numeric(10,2) NOT NULL,
    paid boolean,
    paid_at timestamp without time zone,
    session_id integer,
    created_at timestamp without time zone
);


ALTER TABLE public.delivery_debts OWNER TO fee_maison_user;

--
-- Name: delivery_debts_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.delivery_debts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.delivery_debts_id_seq OWNER TO fee_maison_user;

--
-- Name: delivery_debts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.delivery_debts_id_seq OWNED BY public.delivery_debts.id;


--
-- Name: deliverymen; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.deliverymen (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    phone character varying(20)
);


ALTER TABLE public.deliverymen OWNER TO fee_maison_user;

--
-- Name: deliverymen_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.deliverymen_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.deliverymen_id_seq OWNER TO fee_maison_user;

--
-- Name: deliverymen_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.deliverymen_id_seq OWNED BY public.deliverymen.id;


--
-- Name: employees; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.employees (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    role character varying(50),
    salaire_fixe numeric(10,2),
    prime numeric(10,2),
    is_active boolean,
    created_at timestamp without time zone,
    notes text
);


ALTER TABLE public.employees OWNER TO fee_maison_user;

--
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.employees_id_seq OWNER TO fee_maison_user;

--
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- Name: order_employees; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.order_employees (
    order_id integer NOT NULL,
    employee_id integer NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.order_employees OWNER TO fee_maison_user;

--
-- Name: order_items; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.order_items (
    id integer NOT NULL,
    order_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity numeric(10,3) NOT NULL,
    unit_price numeric(10,2) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.order_items OWNER TO fee_maison_user;

--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.order_items_id_seq OWNER TO fee_maison_user;

--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.order_items_id_seq OWNED BY public.order_items.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    user_id integer,
    order_type character varying(50) NOT NULL,
    customer_name character varying(200),
    customer_phone character varying(20),
    customer_address text,
    delivery_option character varying(20),
    due_date timestamp without time zone NOT NULL,
    delivery_cost numeric(10,2),
    status character varying(50),
    notes text,
    total_amount numeric(10,2),
    created_at timestamp without time zone,
    deliveryman_id integer
);


ALTER TABLE public.orders OWNER TO fee_maison_user;

--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.orders_id_seq OWNER TO fee_maison_user;

--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.products (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    product_type character varying(50) NOT NULL,
    description text,
    price numeric(10,2),
    cost_price numeric(10,4),
    unit character varying(20) NOT NULL,
    sku character varying(50),
    quantity_in_stock double precision,
    category_id integer,
    created_at timestamp without time zone,
    stock_comptoir double precision NOT NULL,
    stock_ingredients_local double precision NOT NULL,
    stock_ingredients_magasin double precision NOT NULL,
    stock_consommables double precision NOT NULL,
    total_stock_value numeric(12,4) DEFAULT 0.0 NOT NULL,
    seuil_min_comptoir double precision,
    seuil_min_ingredients_local double precision,
    seuil_min_ingredients_magasin double precision,
    seuil_min_consommables double precision,
    last_stock_update timestamp without time zone,
    valeur_stock_ingredients_magasin numeric(12,4) DEFAULT 0.0 NOT NULL,
    valeur_stock_ingredients_local numeric(12,4) DEFAULT 0.0 NOT NULL,
    image_filename character varying(255)
);


ALTER TABLE public.products OWNER TO fee_maison_user;

--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.products_id_seq OWNER TO fee_maison_user;

--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: purchase_items; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.purchase_items (
    id integer NOT NULL,
    purchase_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity_ordered numeric(10,3) NOT NULL,
    unit_price numeric(10,2) NOT NULL,
    discount_percentage numeric(5,2),
    original_quantity numeric(10,3),
    original_unit_id integer,
    original_unit_price numeric(10,2),
    quantity_received numeric(10,3),
    stock_location character varying(50) NOT NULL,
    description_override character varying(255),
    supplier_reference character varying(100),
    notes text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.purchase_items OWNER TO fee_maison_user;

--
-- Name: purchase_items_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.purchase_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.purchase_items_id_seq OWNER TO fee_maison_user;

--
-- Name: purchase_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.purchase_items_id_seq OWNED BY public.purchase_items.id;


--
-- Name: purchases; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.purchases (
    id integer NOT NULL,
    reference character varying(50) NOT NULL,
    supplier_name character varying(200) NOT NULL,
    supplier_contact character varying(100),
    supplier_phone character varying(20),
    supplier_email character varying(120),
    supplier_address text,
    status public.purchasestatus NOT NULL,
    urgency public.purchaseurgency NOT NULL,
    requested_by_id integer NOT NULL,
    approved_by_id integer,
    received_by_id integer,
    requested_date timestamp without time zone NOT NULL,
    approved_date timestamp without time zone,
    expected_delivery_date timestamp without time zone,
    received_date timestamp without time zone,
    is_paid boolean,
    payment_date date,
    subtotal_amount numeric(10,2),
    tax_amount numeric(10,2),
    shipping_cost numeric(10,2),
    total_amount numeric(10,2),
    notes text,
    internal_notes text,
    terms_conditions text,
    payment_terms character varying(100),
    default_stock_location character varying(50),
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.purchases OWNER TO fee_maison_user;

--
-- Name: purchases_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.purchases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.purchases_id_seq OWNER TO fee_maison_user;

--
-- Name: purchases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.purchases_id_seq OWNED BY public.purchases.id;


--
-- Name: recipe_ingredients; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.recipe_ingredients (
    id integer NOT NULL,
    recipe_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity_needed numeric(10,3) NOT NULL,
    unit character varying(50) NOT NULL,
    notes character varying(255),
    created_at timestamp without time zone
);


ALTER TABLE public.recipe_ingredients OWNER TO fee_maison_user;

--
-- Name: recipe_ingredients_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.recipe_ingredients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.recipe_ingredients_id_seq OWNER TO fee_maison_user;

--
-- Name: recipe_ingredients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.recipe_ingredients_id_seq OWNED BY public.recipe_ingredients.id;


--
-- Name: recipes; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.recipes (
    id integer NOT NULL,
    name character varying(200) NOT NULL,
    description text,
    product_id integer,
    yield_quantity integer DEFAULT 1 NOT NULL,
    yield_unit character varying(50) DEFAULT 'pièces'::character varying NOT NULL,
    preparation_time integer,
    cooking_time integer,
    difficulty_level character varying(20),
    created_at timestamp without time zone,
    production_location character varying(50) DEFAULT 'ingredients_magasin'::character varying NOT NULL
);


ALTER TABLE public.recipes OWNER TO fee_maison_user;

--
-- Name: recipes_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.recipes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.recipes_id_seq OWNER TO fee_maison_user;

--
-- Name: recipes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.recipes_id_seq OWNED BY public.recipes.id;


--
-- Name: stock_movements; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.stock_movements (
    id integer NOT NULL,
    reference character varying(50) NOT NULL,
    product_id integer NOT NULL,
    stock_location public.stocklocationtype NOT NULL,
    movement_type public.stockmovementtype NOT NULL,
    quantity double precision NOT NULL,
    unit_cost double precision,
    total_value double precision,
    stock_before double precision,
    stock_after double precision,
    order_id integer,
    transfer_id integer,
    user_id integer NOT NULL,
    reason character varying(255),
    notes text,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.stock_movements OWNER TO fee_maison_user;

--
-- Name: stock_movements_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.stock_movements_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stock_movements_id_seq OWNER TO fee_maison_user;

--
-- Name: stock_movements_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.stock_movements_id_seq OWNED BY public.stock_movements.id;


--
-- Name: stock_transfer_lines; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.stock_transfer_lines (
    id integer NOT NULL,
    transfer_id integer NOT NULL,
    product_id integer NOT NULL,
    quantity_requested double precision NOT NULL,
    quantity_approved double precision,
    quantity_transferred double precision,
    unit_cost double precision,
    notes character varying(255),
    created_at timestamp without time zone
);


ALTER TABLE public.stock_transfer_lines OWNER TO fee_maison_user;

--
-- Name: stock_transfer_lines_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.stock_transfer_lines_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stock_transfer_lines_id_seq OWNER TO fee_maison_user;

--
-- Name: stock_transfer_lines_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.stock_transfer_lines_id_seq OWNED BY public.stock_transfer_lines.id;


--
-- Name: stock_transfers; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.stock_transfers (
    id integer NOT NULL,
    reference character varying(50) NOT NULL,
    source_location public.stocklocationtype NOT NULL,
    destination_location public.stocklocationtype NOT NULL,
    status public.transferstatus NOT NULL,
    requested_by_id integer NOT NULL,
    approved_by_id integer,
    completed_by_id integer,
    requested_date timestamp without time zone NOT NULL,
    approved_date timestamp without time zone,
    scheduled_date timestamp without time zone,
    completed_date timestamp without time zone,
    reason character varying(255),
    notes text,
    priority character varying(20)
);


ALTER TABLE public.stock_transfers OWNER TO fee_maison_user;

--
-- Name: stock_transfers_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.stock_transfers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.stock_transfers_id_seq OWNER TO fee_maison_user;

--
-- Name: stock_transfers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.stock_transfers_id_seq OWNED BY public.stock_transfers.id;


--
-- Name: units; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.units (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    base_unit character varying(10) NOT NULL,
    conversion_factor numeric(10,3) NOT NULL,
    unit_type character varying(20) NOT NULL,
    display_order integer,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.units OWNER TO fee_maison_user;

--
-- Name: units_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.units_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.units_id_seq OWNER TO fee_maison_user;

--
-- Name: units_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.units_id_seq OWNED BY public.units.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: fee_maison_user
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(80) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO fee_maison_user;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: fee_maison_user
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO fee_maison_user;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: fee_maison_user
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: cash_movement id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.cash_movement ALTER COLUMN id SET DEFAULT nextval('public.cash_movement_id_seq'::regclass);


--
-- Name: cash_register_session id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.cash_register_session ALTER COLUMN id SET DEFAULT nextval('public.cash_register_session_id_seq'::regclass);


--
-- Name: categories id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.categories ALTER COLUMN id SET DEFAULT nextval('public.categories_id_seq'::regclass);


--
-- Name: delivery_debts id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.delivery_debts ALTER COLUMN id SET DEFAULT nextval('public.delivery_debts_id_seq'::regclass);


--
-- Name: deliverymen id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.deliverymen ALTER COLUMN id SET DEFAULT nextval('public.deliverymen_id_seq'::regclass);


--
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: purchase_items id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items ALTER COLUMN id SET DEFAULT nextval('public.purchase_items_id_seq'::regclass);


--
-- Name: purchases id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases ALTER COLUMN id SET DEFAULT nextval('public.purchases_id_seq'::regclass);


--
-- Name: recipe_ingredients id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipe_ingredients ALTER COLUMN id SET DEFAULT nextval('public.recipe_ingredients_id_seq'::regclass);


--
-- Name: recipes id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipes ALTER COLUMN id SET DEFAULT nextval('public.recipes_id_seq'::regclass);


--
-- Name: stock_movements id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements ALTER COLUMN id SET DEFAULT nextval('public.stock_movements_id_seq'::regclass);


--
-- Name: stock_transfer_lines id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfer_lines ALTER COLUMN id SET DEFAULT nextval('public.stock_transfer_lines_id_seq'::regclass);


--
-- Name: stock_transfers id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers ALTER COLUMN id SET DEFAULT nextval('public.stock_transfers_id_seq'::regclass);


--
-- Name: units id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.units ALTER COLUMN id SET DEFAULT nextval('public.units_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.alembic_version (version_num) FROM stdin;
5a7dc22f426f
\.


--
-- Data for Name: cash_movement; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.cash_movement (id, session_id, created_at, type, amount, reason, employee_id, notes) FROM stdin;
1	2	2025-07-01 02:11:09.869001	entrée	150	Vente	1	\N
2	2	2025-07-01 02:11:09.870306	sortie	50	Achat fournitures	1	\N
3	4	2025-07-01 02:11:49.053034	entrée	150	Vente	1	\N
4	4	2025-07-01 02:11:49.053833	sortie	50	Achat fournitures	1	\N
5	7	2025-07-01 02:31:51.914023	entrée	200	Vente POS - 2 article(s)	1	Vente directe: 2x Mhadjeb
6	8	2025-07-01 02:32:15.692162	entrée	140	Vente POS - 2 article(s)	1	Vente directe: 2x Msamen Grand Taille
7	8	2025-07-01 02:32:15.701693	entrée	150	Vente commande #123	1	Commande client: 1x Msamen Grand Taille
8	9	2025-07-01 02:45:52.568054	entrée	200	Vente commande #18	1	Commande client: 2x Mhadjeb
9	13	2025-07-02 00:31:57.832808	entrée	570	Paiement commande #21 (delivery)	1	Encaissement commande client: Mohamed LIF
\.


--
-- Data for Name: cash_register_session; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.cash_register_session (id, opened_at, closed_at, initial_amount, closing_amount, opened_by_id, closed_by_id, is_open) FROM stdin;
1	2025-06-29 03:50:54.864795	2025-07-01 02:11:09.782072	10000	\N	1	\N	f
2	2025-07-01 02:11:09.814586	2025-07-01 02:11:09.883686	1000	1100	1	1	f
3	2025-07-01 02:11:09.824293	2025-07-01 02:11:37.631335	500	\N	1	\N	f
4	2025-07-01 02:11:49.037024	2025-07-01 02:11:49.103879	1000	1100	1	1	f
5	2025-07-01 02:11:49.048859	2025-07-01 02:14:37.124138	500	500	1	1	f
6	2025-07-01 02:14:54.222725	2025-07-01 02:16:21.989138	10000	9000	1	1	f
7	2025-07-01 02:31:51.901224	2025-07-01 02:32:15.678679	1000	\N	1	\N	f
8	2025-07-01 02:32:15.682507	2025-07-01 02:32:15.706875	1000	1290	1	1	f
9	2025-07-01 02:37:27.666991	2025-07-02 00:01:44.558353	9000	9000	1	1	f
10	2025-07-02 00:07:23.186432	2025-07-02 00:10:36.117952	10000	10000	1	1	f
11	2025-07-02 00:11:49.544833	2025-07-02 00:18:14.849048	10000	10000	1	1	f
12	2025-07-02 00:19:36.448499	2025-07-02 00:20:26.559323	10000	10000	1	1	f
13	2025-07-02 00:20:41.113953	\N	10000	\N	1	\N	t
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.categories (id, name, description, created_at) FROM stdin;
1	Ingrédients		2025-06-26 03:26:34.342911
2	Pâtes		2025-06-26 03:26:51.438184
4	Test Category	Catégorie pour tests	2025-07-01 23:18:42.488418
\.


--
-- Data for Name: delivery_debts; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.delivery_debts (id, order_id, deliveryman_id, amount, paid, paid_at, session_id, created_at) FROM stdin;
\.


--
-- Data for Name: deliverymen; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.deliverymen (id, name, phone) FROM stdin;
1	Idir	0542604527
\.


--
-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.employees (id, name, role, salaire_fixe, prime, is_active, created_at, notes) FROM stdin;
1	Saida	production	30000.00	0.00	t	2025-06-29 00:04:55.246609	
2	Fatiha	production	35000.00	0.00	t	2025-06-29 00:05:35.009115	
\.


--
-- Data for Name: order_employees; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.order_employees (order_id, employee_id, created_at) FROM stdin;
2	2	2025-06-29 00:05:56.90704
3	1	2025-06-29 00:32:52.846114
6	2	2025-06-29 00:48:49.517125
7	2	2025-06-29 01:06:20.456812
8	1	2025-06-29 01:21:11.616925
13	2	2025-06-30 03:27:02.431102
14	1	2025-07-01 00:46:54.039044
19	2	2025-07-01 02:52:17.393118
20	1	2025-07-01 03:57:16.025565
22	2	2025-07-02 23:19:00.226842
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.order_items (id, order_id, product_id, quantity, unit_price, created_at) FROM stdin;
1	1	4	10.000	0.00	2025-06-28 23:52:31.651467
2	2	4	10.000	0.00	2025-06-29 00:01:28.410767
3	3	4	10.000	0.00	2025-06-29 00:32:29.31646
4	4	4	5.000	70.00	2025-06-29 00:42:11.406928
5	5	4	5.000	70.00	2025-06-29 00:42:36.495315
6	6	4	10.000	0.00	2025-06-29 00:48:22.023605
7	7	4	10.000	0.00	2025-06-29 01:05:56.324967
8	8	4	10.000	0.00	2025-06-29 01:20:49.403344
10	10	4	2.000	70.00	2025-06-30 01:24:13.991137
11	11	4	1.000	70.00	2025-06-30 01:25:19.615455
12	12	4	1.000	70.00	2025-06-30 01:26:29.604277
13	13	4	10.000	0.00	2025-06-30 03:26:13.320535
14	14	5	10.000	0.00	2025-07-01 00:46:29.327584
15	15	5	2.000	100.00	2025-07-01 02:14:14.598029
16	16	5	2.000	100.00	2025-07-01 02:15:02.846281
17	17	5	2.000	100.00	2025-07-01 02:15:10.412785
18	17	4	1.000	70.00	2025-07-01 02:15:10.415889
19	18	5	2.000	100.00	2025-07-01 02:45:52.566157
20	19	4	1.000	70.00	2025-07-01 02:47:28.351232
21	20	4	1.000	70.00	2025-07-01 03:52:38.03018
22	21	4	1.000	70.00	2025-07-02 00:28:44.510352
23	22	4	1.000	70.00	2025-07-02 23:15:43.106606
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.orders (id, user_id, order_type, customer_name, customer_phone, customer_address, delivery_option, due_date, delivery_cost, status, notes, total_amount, created_at, deliveryman_id) FROM stdin;
1	1	counter_production_request	\N	\N	\N	pickup	2025-06-29 13:00:00	0.00	cancelled		0.00	2025-06-28 23:52:31.604425	\N
2	1	counter_production_request	\N	\N	\N	pickup	2025-06-29 13:00:00	0.00	completed		0.00	2025-06-29 00:01:28.406352	\N
3	1	counter_production_request	\N	\N	\N	pickup	2025-06-29 14:00:00	0.00	completed		0.00	2025-06-29 00:32:29.312626	\N
5	\N	counter_production_request	\N	\N	\N	pickup	2025-06-29 02:42:36.387644	0.00	ready_at_shop	\N	0.00	2025-06-29 00:42:36.483162	\N
4	\N	counter_production_request	\N	\N	\N	pickup	2025-06-29 02:42:11.294376	0.00	ready_at_shop	\N	0.00	2025-06-29 00:42:11.395171	\N
6	1	counter_production_request	\N	\N	\N	pickup	2025-06-29 14:30:00	0.00	completed		0.00	2025-06-29 00:48:22.019352	\N
7	1	counter_production_request	\N	\N	\N	pickup	2025-06-29 13:50:00	0.00	completed		0.00	2025-06-29 01:05:56.322495	\N
8	1	counter_production_request	\N	\N	\N	pickup	2025-06-29 16:00:00	0.00	completed		0.00	2025-06-29 01:20:49.398724	\N
10	1	in_store	Vente directe	\N	\N	pickup	2025-06-30 01:24:13.968556	0.00	completed	\N	140.00	2025-06-30 01:24:13.971386	\N
11	1	in_store	Vente directe	\N	\N	pickup	2025-06-30 01:25:19.602298	0.00	completed	\N	70.00	2025-06-30 01:25:19.602755	\N
12	1	in_store	Vente directe	\N	\N	pickup	2025-06-30 01:26:29.600521	0.00	completed	\N	70.00	2025-06-30 01:26:29.600902	\N
13	1	counter_production_request	\N	\N	\N	pickup	2025-06-30 13:00:00	0.00	completed		0.00	2025-06-30 03:26:13.315427	\N
14	1	counter_production_request	\N	\N	\N	pickup	2025-07-01 13:00:00	0.00	completed		0.00	2025-07-01 00:46:29.282191	\N
15	1	in_store	Vente directe	\N	\N	pickup	2025-07-01 02:14:14.579095	0.00	completed	\N	200.00	2025-07-01 02:14:14.585653	\N
16	1	in_store	Vente directe	\N	\N	pickup	2025-07-01 02:15:02.841518	0.00	completed	\N	200.00	2025-07-01 02:15:02.842119	\N
17	1	in_store	Vente directe	\N	\N	pickup	2025-07-01 02:15:10.408214	0.00	completed	\N	270.00	2025-07-01 02:15:10.408674	\N
18	1	in_store	Vente directe	\N	\N	pickup	2025-07-01 02:45:52.544758	0.00	completed	\N	200.00	2025-07-01 02:45:52.554888	\N
19	1	customer_order	Mohamed LIF	0556246858		pickup	2025-07-01 13:00:00	0.00	completed		70.00	2025-07-01 02:47:28.349372	\N
21	1	customer_order	Mohamed LIF	0556246858	Rue Fadhel Abd El Kader\r\n23	delivery	2025-07-02 13:00:00	500.00	out_for_delivery		570.00	2025-07-02 00:28:44.505739	\N
20	1	customer_order	Hamid	0552525252	Cheraga	delivery	2025-07-01 14:00:00	500.00	delivered		570.00	2025-07-01 03:52:37.985522	\N
22	1	customer_order	Sihem	0552222222	Cheraga	delivery	2025-07-03 13:00:00	100.00	ready_at_shop		170.00	2025-07-02 23:15:43.059205	1
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.products (id, name, product_type, description, price, cost_price, unit, sku, quantity_in_stock, category_id, created_at, stock_comptoir, stock_ingredients_local, stock_ingredients_magasin, stock_consommables, total_stock_value, seuil_min_comptoir, seuil_min_ingredients_local, seuil_min_ingredients_magasin, seuil_min_consommables, last_stock_update, valeur_stock_ingredients_magasin, valeur_stock_ingredients_local, image_filename) FROM stdin;
8	Tomate Conserve	ingredient		\N	4.3723	g	TOMTCNSV	0	1	2025-06-28 03:00:51.425934	0	3000	9973.214285714286	0	56722.8848	0	0	0	0	2025-07-01 00:46:54.015991	55882.8848	840.0000	\N
7	Paprika	ingredient		\N	1.5000	g	PAPRIKA	0	1	2025-06-28 02:59:38.224002	0	1000	991.0714285714286	0	2986.6071	0	0	0	0	2025-07-01 00:46:54.017729	1486.6071	1500.0000	\N
9	Produit Test Selenium	ingredient	Produit pour tests automatisés	15.00	10.0000	kg	TEST-SELENIUM-001	100	4	2025-07-01 23:18:42.498568	100	25	50	10	0.0000	0	0	0	0	2025-07-01 23:18:42.498575	0.0000	0.0000	\N
2	Huile Civital	ingredient		\N	0.3379	ml	HUIL	0	1	2025-06-26 03:31:45.974415	0	5000	4156.25	0	3094.1293	0	0	0	0	2025-07-02 23:19:00.200725	2574.4864	600.0000	\N
3	Sel	ingredient		\N	0.0728	g	SEL	0	1	2025-06-26 03:32:40.309076	0	1000	906.6964285714289	0	138.7370	0	0	0	0	2025-07-02 23:19:00.205762	115.4111	25.0000	\N
1	Semoule Fin	ingredient		\N	0.1433	g	SEMLFIN	0	1	2025-06-26 03:28:48.809964	0	25000	30499.99999999999	0	7953.5072	0	0	0	0	2025-07-02 23:19:00.208283	7064.2215	1050.0000	\N
4	Msamen Grand Taille	finished		70.00	69.8985	pièce	MSMNG	0	2	2025-06-26 03:33:47.776701	11	0	0	0	768.8832	0	0	0	0	2025-07-02 23:19:00.210183	0.0000	0.0000	msamen.jpg
5	Mhadjeb	finished		100.00	39.1352	pièce	MHDJB	0	2	2025-06-28 01:59:18.911148	0	0	0	0	78.2702	0	0	0	0	2025-07-01 02:45:52.559066	0.0000	0.0000	Mhadjeb.jpeg
6	Oignon	ingredient		\N	0.0500	g	OIGN	0	1	2025-06-28 02:58:23.189449	0	10000	32767.85714285714	0	2138.3929	0	0	0	0	2025-07-01 00:46:54.013414	1638.3929	500.0000	\N
\.


--
-- Data for Name: purchase_items; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.purchase_items (id, purchase_id, product_id, quantity_ordered, unit_price, discount_percentage, original_quantity, original_unit_id, original_unit_price, quantity_received, stock_location, description_override, supplier_reference, notes, created_at, updated_at) FROM stdin;
1	1	1	25000.000	0.04	0.00	1.000	1	1050.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 03:35:11.17145	2025-06-28 03:35:11.171456
2	1	2	5000.000	0.12	0.00	1.000	15	600.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 03:35:11.219051	2025-06-28 03:35:11.219057
3	1	3	1000.000	0.03	0.00	1.000	5	25.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 03:35:11.223286	2025-06-28 03:35:11.223292
4	2	1	25000.000	0.04	0.00	1.000	1	1050.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 03:51:28.347811	2025-06-28 03:51:28.347816
5	2	2	5000.000	0.12	0.00	1.000	15	600.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 03:51:28.35192	2025-06-28 03:51:28.351927
6	2	3	1000.000	0.03	0.00	1.000	5	25.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 03:51:28.355723	2025-06-28 03:51:28.355729
7	3	1	25000.000	0.04	0.00	1.000	1	1050.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 04:01:51.841854	2025-06-28 04:01:51.84186
8	3	2	5000.000	0.12	0.00	1.000	15	600.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 04:01:51.847567	2025-06-28 04:01:51.847573
9	3	3	1000.000	0.03	0.00	1.000	5	25.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 04:01:51.850723	2025-06-28 04:01:51.850728
10	4	1	25000.000	0.04	0.00	1.000	1	1050.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 23:27:47.763642	2025-06-28 23:27:47.763649
11	4	3	1000.000	0.03	0.00	1.000	5	25.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 23:27:47.814667	2025-06-28 23:27:47.814673
12	4	2	5000.000	0.12	0.00	1.000	15	600.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 23:27:47.822507	2025-06-28 23:27:47.822512
13	5	1	25000.000	0.04	0.00	1.000	1	1050.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 23:31:18.533201	2025-06-28 23:31:18.533206
14	6	1	25000.000	0.04	0.00	1.000	1	1050.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 23:34:22.039004	2025-06-28 23:34:22.039009
15	7	1	25000.000	0.04	0.00	1.000	1	1050.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 23:36:16.570506	2025-06-28 23:36:16.570512
16	8	1	10000.000	0.06	0.00	1.000	2	600.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 23:42:41.148562	2025-06-28 23:42:41.148569
17	8	2	5000.000	0.12	0.00	1.000	15	600.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-28 23:42:41.155611	2025-06-28 23:42:41.155615
18	9	3	1000.000	0.03	0.00	1.000	5	25.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-29 00:03:11.132527	2025-06-29 00:03:11.132533
19	10	1	25000.000	0.04	0.00	1.000	1	1050.00	0.000	ingredients_local	\N	\N	\N	2025-06-30 02:01:06.756156	2025-06-30 02:01:06.756162
20	10	3	1000.000	0.03	0.00	1.000	5	25.00	0.000	ingredients_local	\N	\N	\N	2025-06-30 02:01:06.847136	2025-06-30 02:01:06.847142
21	10	2	5000.000	0.12	0.00	1.000	15	600.00	0.000	ingredients_local	\N	\N	\N	2025-06-30 02:01:06.853707	2025-06-30 02:01:06.853713
30	12	8	3000.000	0.28	0.00	6.000	10	140.00	0.000	ingredients_local	\N	\N	\N	2025-06-30 02:43:49.718436	2025-06-30 02:43:49.718441
31	11	7	1000.000	1.50	0.00	1.000	5	1500.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-30 02:44:20.85856	2025-06-30 02:44:20.858566
32	11	6	10000.000	0.05	0.00	1.000	2	500.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-30 02:44:20.864113	2025-06-30 02:44:20.86412
33	11	8	10000.000	0.28	0.00	20.000	10	140.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-30 02:44:20.869767	2025-06-30 02:44:20.869771
34	13	6	10000.000	0.05	0.00	1.000	2	500.00	0.000	ingredients_local	\N	\N	\N	2025-06-30 02:46:06.119178	2025-06-30 02:46:06.119184
35	13	7	1000.000	1.50	0.00	1.000	5	1500.00	0.000	ingredients_local	\N	\N	\N	2025-06-30 02:46:06.124511	2025-06-30 02:46:06.124517
36	14	6	25000.000	0.05	0.00	1.000	1	1250.00	0.000	ingredients_magasin	\N	\N	\N	2025-06-30 02:50:05.493077	2025-06-30 02:50:05.493086
\.


--
-- Data for Name: purchases; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.purchases (id, reference, supplier_name, supplier_contact, supplier_phone, supplier_email, supplier_address, status, urgency, requested_by_id, approved_by_id, received_by_id, requested_date, approved_date, expected_delivery_date, received_date, is_paid, payment_date, subtotal_amount, tax_amount, shipping_cost, total_amount, notes, internal_notes, terms_conditions, payment_terms, default_stock_location, created_at, updated_at) FROM stdin;
1	BA2025-AC6EC659	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-27 03:30:00	\N	\N	\N	t	2025-06-28	1625.00	0.00	0.00	1625.00		\N	\N	\N	ingredients_magasin	2025-06-28 03:35:11.110414	2025-06-28 03:35:51.412421
2	BA2025-141CB7C5	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-26 03:49:00	\N	\N	\N	t	2025-06-27	1625.00	0.00	0.00	1625.00		\N	\N	\N	ingredients_magasin	2025-06-28 03:51:28.338028	2025-06-28 03:51:46.509303
3	BA2025-DDAC6D48	Sofiane	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-25 04:00:00	\N	\N	\N	t	2025-06-28	1625.00	0.00	0.00	1625.00		\N	\N	\N	ingredients_magasin	2025-06-28 04:01:51.82972	2025-06-28 04:02:00.806935
4	BA2025-917A317C	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-23 23:26:00	\N	\N	\N	t	2025-06-29	1630.00	0.00	0.00	1630.00		\N	\N	\N	ingredients_magasin	2025-06-28 23:27:47.702147	2025-06-28 23:27:55.776602
5	BA2025-A5EAE518	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-28 23:30:00	\N	\N	\N	t	2025-06-29	1050.00	0.00	0.00	1050.00		\N	\N	\N	ingredients_magasin	2025-06-28 23:31:18.522059	2025-06-28 23:31:25.411981
6	BA2025-A1B7EB0F	Sofiane	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-28 23:33:00	\N	\N	\N	t	2025-06-29	1050.00	0.00	0.00	1050.00		\N	\N	\N	ingredients_magasin	2025-06-28 23:34:22.028709	2025-06-28 23:34:28.681545
7	BA2025-CA514DC8	Slimane	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-28 23:35:00	\N	\N	\N	t	2025-06-29	1050.00	0.00	0.00	1050.00		\N	\N	\N	ingredients_magasin	2025-06-28 23:36:16.559628	2025-06-28 23:36:22.712387
8	BA2025-B3FBA06C	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-28 23:41:00	\N	\N	\N	t	2025-06-29	1200.00	0.00	0.00	1200.00		\N	\N	\N	ingredients_magasin	2025-06-28 23:42:41.139881	2025-06-28 23:42:47.548554
9	BA2025-3A23442A	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-29 00:02:00	\N	\N	\N	t	2025-06-29	25.00	0.00	0.00	25.00		\N	\N	\N	ingredients_magasin	2025-06-29 00:03:11.122189	2025-06-29 00:03:18.547949
10	BA2025-5EEF3357	Morad	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-30 01:59:00	\N	\N	\N	t	2025-06-30	1630.00	0.00	0.00	1630.00		\N	\N	\N	ingredients_magasin	2025-06-30 02:01:06.655802	2025-06-30 02:01:23.969201
12	BA2025-34893A44	Halim					RECEIVED	NORMAL	1	\N	\N	2025-06-30 02:41:00	\N	\N	\N	t	2025-06-30	840.00	0.00	0.00	840.00		\N	\N	\N	ingredients_magasin	2025-06-30 02:42:43.942932	2025-06-30 02:43:49.716983
11	BA2025-4485CAA8	Slimane					RECEIVED	NORMAL	1	\N	\N	2025-06-30 02:01:00	\N	\N	\N	t	2025-06-30	4800.00	0.00	0.00	4800.00		\N	\N	\N	ingredients_magasin	2025-06-30 02:04:13.406979	2025-06-30 02:44:20.868342
13	BA2025-2A3838D4	Slimane	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-30 02:44:00	\N	\N	\N	t	2025-06-30	2000.00	0.00	0.00	2000.00		\N	\N	\N	ingredients_magasin	2025-06-30 02:46:06.111757	2025-06-30 02:46:19.124894
14	BA2025-6A4AC10A	Bilel	\N	\N	\N	\N	RECEIVED	NORMAL	1	\N	\N	2025-06-30 02:49:00	\N	\N	\N	t	2025-06-30	1250.00	0.00	0.00	1250.00		\N	\N	\N	ingredients_magasin	2025-06-30 02:50:05.484577	2025-06-30 02:50:15.358982
\.


--
-- Data for Name: recipe_ingredients; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.recipe_ingredients (id, recipe_id, product_id, quantity_needed, unit, notes, created_at) FROM stdin;
1	1	2	1500.000	ml	\N	2025-06-26 03:34:57.341751
2	1	3	150.000	g	\N	2025-06-26 03:34:57.341758
3	1	1	8000.000	g	\N	2025-06-26 03:34:57.34176
4	2	1	8000.000	g	\N	2025-06-30 23:47:28.330471
5	2	3	250.000	g	\N	2025-06-30 23:47:28.330478
6	2	2	1500.000	ml	\N	2025-06-30 23:47:28.33048
7	2	6	25000.000	g	\N	2025-06-30 23:47:28.330482
8	2	8	300.000	g	\N	2025-06-30 23:47:28.330483
9	2	7	100.000	g	\N	2025-06-30 23:47:28.330484
\.


--
-- Data for Name: recipes; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.recipes (id, name, description, product_id, yield_quantity, yield_unit, preparation_time, cooking_time, difficulty_level, created_at, production_location) FROM stdin;
1	MSGT		4	112	pièces	\N	\N	\N	2025-06-26 03:34:57.29699	ingredients_magasin
2	MHADJEBGT		5	112	pièces	\N	\N	\N	2025-06-30 23:47:28.284682	ingredients_magasin
\.


--
-- Data for Name: stock_movements; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.stock_movements (id, reference, product_id, stock_location, movement_type, quantity, unit_cost, total_value, stock_before, stock_after, order_id, transfer_id, user_id, reason, notes, created_at) FROM stdin;
\.


--
-- Data for Name: stock_transfer_lines; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.stock_transfer_lines (id, transfer_id, product_id, quantity_requested, quantity_approved, quantity_transferred, unit_cost, notes, created_at) FROM stdin;
\.


--
-- Data for Name: stock_transfers; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.stock_transfers (id, reference, source_location, destination_location, status, requested_by_id, approved_by_id, completed_by_id, requested_date, approved_date, scheduled_date, completed_date, reason, notes, priority) FROM stdin;
\.


--
-- Data for Name: units; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.units (id, name, base_unit, conversion_factor, unit_type, display_order, is_active, created_at) FROM stdin;
1	Sac 25kg	g	25000.000	Poids	0	t	2025-06-28 03:29:38.722122
2	Sac 10kg	g	10000.000	Poids	0	t	2025-06-28 03:29:38.766172
3	Sac 5kg	g	5000.000	Poids	0	t	2025-06-28 03:29:38.767983
4	Sac 2kg	g	2000.000	Poids	0	t	2025-06-28 03:29:38.770097
5	Sac 1kg	g	1000.000	Poids	0	t	2025-06-28 03:29:38.771604
6	Barre 1,8kg	g	1800.000	Poids	0	t	2025-06-28 03:29:38.773111
7	Bidon 3,8kg	g	3800.000	Poids	0	t	2025-06-28 03:29:38.774748
8	Boite 500g	g	500.000	Poids	0	t	2025-06-28 03:29:38.776082
9	Sachet 500g	g	500.000	Poids	0	t	2025-06-28 03:29:38.778167
10	Pot 500g	g	500.000	Poids	0	t	2025-06-28 03:29:38.77984
11	Boite 250g	g	250.000	Poids	0	t	2025-06-28 03:29:38.781195
12	Sachet 125g	g	125.000	Poids	0	t	2025-06-28 03:29:38.784139
13	Sachet 10g	g	10.000	Poids	0	t	2025-06-28 03:29:38.785886
14	Bidon 5L	ml	5000.000	Volume	0	t	2025-06-28 03:29:38.787291
15	Bouteille 5L	ml	5000.000	Volume	0	t	2025-06-28 03:29:38.788666
16	Bouteille 2L	ml	2000.000	Volume	0	t	2025-06-28 03:29:38.789743
17	Bouteille 1L	ml	1000.000	Volume	0	t	2025-06-28 03:29:38.79091
18	Lot de 100 pièces	pièce	100.000	Unitaire	0	t	2025-06-28 03:29:38.792247
19	Lot de 50 pièces	pièce	50.000	Unitaire	0	t	2025-06-28 03:29:38.793696
20	Plateau de 30 pièces	pièce	30.000	Unitaire	0	t	2025-06-28 03:29:38.795137
21	Lot de 12 pièces	pièce	12.000	Unitaire	0	t	2025-06-28 03:29:38.796677
22	Lot de 10 pièces	pièce	10.000	Unitaire	0	t	2025-06-28 03:29:38.798138
23	Lot de 6 pièces	pièce	6.000	Unitaire	0	t	2025-06-28 03:29:38.799645
24	Fardeau de 6 bouteilles	pièce	6.000	Unitaire	0	t	2025-06-28 03:29:38.801111
25	Gramme (g)	g	1.000	Poids	0	t	2025-06-28 03:29:38.802346
26	Millilitre (ml)	ml	1.000	Volume	0	t	2025-06-28 03:29:38.803515
27	Pièce	pièce	1.000	Unitaire	0	t	2025-06-28 03:29:38.804654
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: fee_maison_user
--

COPY public.users (id, username, email, password_hash, role, created_at) FROM stdin;
1	admin	admin@example.com	scrypt:32768:8:1$NF46JaSJwxIIjiNE$bff29ff1fdb7fbeeca1c1958302b6342a7bf45a4140e644f0dabfb2d2ad54a257470ffe38ba9f0f4101816eb419436b865836993633ecbc35a13422cc52069b0	admin	2025-06-26 01:06:10.441279
\.


--
-- Name: cash_movement_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.cash_movement_id_seq', 9, true);


--
-- Name: cash_register_session_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.cash_register_session_id_seq', 13, true);


--
-- Name: categories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.categories_id_seq', 4, true);


--
-- Name: delivery_debts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.delivery_debts_id_seq', 1, false);


--
-- Name: deliverymen_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.deliverymen_id_seq', 1, true);


--
-- Name: employees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.employees_id_seq', 2, true);


--
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.order_items_id_seq', 23, true);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.orders_id_seq', 22, true);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.products_id_seq', 9, true);


--
-- Name: purchase_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.purchase_items_id_seq', 36, true);


--
-- Name: purchases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.purchases_id_seq', 14, true);


--
-- Name: recipe_ingredients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.recipe_ingredients_id_seq', 9, true);


--
-- Name: recipes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.recipes_id_seq', 2, true);


--
-- Name: stock_movements_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.stock_movements_id_seq', 1, false);


--
-- Name: stock_transfer_lines_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.stock_transfer_lines_id_seq', 1, false);


--
-- Name: stock_transfers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.stock_transfers_id_seq', 1, false);


--
-- Name: units_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.units_id_seq', 27, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: fee_maison_user
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: cash_movement cash_movement_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.cash_movement
    ADD CONSTRAINT cash_movement_pkey PRIMARY KEY (id);


--
-- Name: cash_register_session cash_register_session_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.cash_register_session
    ADD CONSTRAINT cash_register_session_pkey PRIMARY KEY (id);


--
-- Name: categories categories_name_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_name_key UNIQUE (name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: delivery_debts delivery_debts_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.delivery_debts
    ADD CONSTRAINT delivery_debts_pkey PRIMARY KEY (id);


--
-- Name: deliverymen deliverymen_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.deliverymen
    ADD CONSTRAINT deliverymen_pkey PRIMARY KEY (id);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- Name: order_employees order_employees_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_employees
    ADD CONSTRAINT order_employees_pkey PRIMARY KEY (order_id, employee_id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: products products_sku_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_sku_key UNIQUE (sku);


--
-- Name: purchase_items purchase_items_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items
    ADD CONSTRAINT purchase_items_pkey PRIMARY KEY (id);


--
-- Name: purchases purchases_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_pkey PRIMARY KEY (id);


--
-- Name: purchases purchases_reference_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_reference_key UNIQUE (reference);


--
-- Name: recipe_ingredients recipe_ingredients_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT recipe_ingredients_pkey PRIMARY KEY (id);


--
-- Name: recipes recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_pkey PRIMARY KEY (id);


--
-- Name: recipes recipes_product_id_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_product_id_key UNIQUE (product_id);


--
-- Name: stock_movements stock_movements_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_pkey PRIMARY KEY (id);


--
-- Name: stock_movements stock_movements_reference_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_reference_key UNIQUE (reference);


--
-- Name: stock_transfer_lines stock_transfer_lines_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfer_lines
    ADD CONSTRAINT stock_transfer_lines_pkey PRIMARY KEY (id);


--
-- Name: stock_transfers stock_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_pkey PRIMARY KEY (id);


--
-- Name: stock_transfers stock_transfers_reference_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_reference_key UNIQUE (reference);


--
-- Name: units units_name_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_name_key UNIQUE (name);


--
-- Name: units units_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.units
    ADD CONSTRAINT units_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: ix_orders_status; Type: INDEX; Schema: public; Owner: fee_maison_user
--

CREATE INDEX ix_orders_status ON public.orders USING btree (status);


--
-- Name: ix_products_name; Type: INDEX; Schema: public; Owner: fee_maison_user
--

CREATE INDEX ix_products_name ON public.products USING btree (name);


--
-- Name: cash_movement cash_movement_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.cash_movement
    ADD CONSTRAINT cash_movement_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: cash_movement cash_movement_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.cash_movement
    ADD CONSTRAINT cash_movement_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.cash_register_session(id);


--
-- Name: cash_register_session cash_register_session_closed_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.cash_register_session
    ADD CONSTRAINT cash_register_session_closed_by_id_fkey FOREIGN KEY (closed_by_id) REFERENCES public.employees(id);


--
-- Name: cash_register_session cash_register_session_opened_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.cash_register_session
    ADD CONSTRAINT cash_register_session_opened_by_id_fkey FOREIGN KEY (opened_by_id) REFERENCES public.employees(id);


--
-- Name: delivery_debts delivery_debts_deliveryman_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.delivery_debts
    ADD CONSTRAINT delivery_debts_deliveryman_id_fkey FOREIGN KEY (deliveryman_id) REFERENCES public.employees(id);


--
-- Name: delivery_debts delivery_debts_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.delivery_debts
    ADD CONSTRAINT delivery_debts_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: delivery_debts delivery_debts_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.delivery_debts
    ADD CONSTRAINT delivery_debts_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.cash_register_session(id);


--
-- Name: order_employees order_employees_employee_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_employees
    ADD CONSTRAINT order_employees_employee_id_fkey FOREIGN KEY (employee_id) REFERENCES public.employees(id);


--
-- Name: order_employees order_employees_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_employees
    ADD CONSTRAINT order_employees_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: order_items order_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: orders orders_deliveryman_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_deliveryman_id_fkey FOREIGN KEY (deliveryman_id) REFERENCES public.deliverymen(id);


--
-- Name: orders orders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: products products_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: purchase_items purchase_items_original_unit_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items
    ADD CONSTRAINT purchase_items_original_unit_id_fkey FOREIGN KEY (original_unit_id) REFERENCES public.units(id);


--
-- Name: purchase_items purchase_items_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items
    ADD CONSTRAINT purchase_items_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: purchase_items purchase_items_purchase_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchase_items
    ADD CONSTRAINT purchase_items_purchase_id_fkey FOREIGN KEY (purchase_id) REFERENCES public.purchases(id);


--
-- Name: purchases purchases_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- Name: purchases purchases_received_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_received_by_id_fkey FOREIGN KEY (received_by_id) REFERENCES public.users(id);


--
-- Name: purchases purchases_requested_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.purchases
    ADD CONSTRAINT purchases_requested_by_id_fkey FOREIGN KEY (requested_by_id) REFERENCES public.users(id);


--
-- Name: recipe_ingredients recipe_ingredients_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT recipe_ingredients_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: recipe_ingredients recipe_ingredients_recipe_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipe_ingredients
    ADD CONSTRAINT recipe_ingredients_recipe_id_fkey FOREIGN KEY (recipe_id) REFERENCES public.recipes(id);


--
-- Name: recipes recipes_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.recipes
    ADD CONSTRAINT recipes_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: stock_movements stock_movements_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(id);


--
-- Name: stock_movements stock_movements_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: stock_movements stock_movements_transfer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_transfer_id_fkey FOREIGN KEY (transfer_id) REFERENCES public.stock_transfers(id);


--
-- Name: stock_movements stock_movements_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_movements
    ADD CONSTRAINT stock_movements_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: stock_transfer_lines stock_transfer_lines_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfer_lines
    ADD CONSTRAINT stock_transfer_lines_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id);


--
-- Name: stock_transfer_lines stock_transfer_lines_transfer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfer_lines
    ADD CONSTRAINT stock_transfer_lines_transfer_id_fkey FOREIGN KEY (transfer_id) REFERENCES public.stock_transfers(id);


--
-- Name: stock_transfers stock_transfers_approved_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_approved_by_id_fkey FOREIGN KEY (approved_by_id) REFERENCES public.users(id);


--
-- Name: stock_transfers stock_transfers_completed_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_completed_by_id_fkey FOREIGN KEY (completed_by_id) REFERENCES public.users(id);


--
-- Name: stock_transfers stock_transfers_requested_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: fee_maison_user
--

ALTER TABLE ONLY public.stock_transfers
    ADD CONSTRAINT stock_transfers_requested_by_id_fkey FOREIGN KEY (requested_by_id) REFERENCES public.users(id);


--
-- PostgreSQL database dump complete
--

