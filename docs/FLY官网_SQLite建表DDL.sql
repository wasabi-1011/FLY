-- ============================================================
-- FLY 品牌官网 · SQLite 建表脚本
-- 基础由 backend/.venv 内 SQLAlchemy 2.0.52 方言编译导出。
-- 例外：items.price（记录字段，数据库设计文档 v1.1 / PRD v1.6 新增）
-- 为手工补入，ORM 模型暂未映射——若以 SQLAlchemy create_all 建库将不包含此列。
-- v1.2（商品域层级重构 v2.2）：items 增 category（必填）并删除 collection_id；
-- collections 瘦身为 名称/年份/季节/封面/状态，改用 item_id FK 挂在 items 下。
-- ============================================================

-- ========== admin_login_logs ==========
CREATE TABLE admin_login_logs (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	username VARCHAR(100) NOT NULL, 
	success BOOLEAN NOT NULL, 
	fail_reason VARCHAR(100), 
	ip VARCHAR(64), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_admin_login_logs_created_at ON admin_login_logs (created_at);
CREATE INDEX ix_admin_login_logs_user_id ON admin_login_logs (user_id);

-- ========== admin_users ==========
CREATE TABLE admin_users (
	id INTEGER NOT NULL, 
	username VARCHAR(100) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(15) NOT NULL, 
	status VARCHAR(8) NOT NULL, 
	last_login_at DATETIME, 
	failed_attempts INTEGER NOT NULL, 
	locked_until DATETIME, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_admin_users_username ON admin_users (username);

-- ========== articles ==========
CREATE TABLE articles (
	id INTEGER NOT NULL, 
	title VARCHAR(300) NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	category VARCHAR(8) NOT NULL, 
	cover_image VARCHAR(512), 
	summary VARCHAR(500), 
	content TEXT, 
	author VARCHAR(100), 
	published_at DATETIME, 
	status VARCHAR(7) NOT NULL, 
	seo_title VARCHAR(200), 
	seo_description VARCHAR(300), 
	og_image VARCHAR(512), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_articles_category ON articles (category);
CREATE INDEX ix_articles_published_at ON articles (published_at);
CREATE UNIQUE INDEX ix_articles_slug ON articles (slug);
CREATE INDEX ix_articles_status ON articles (status);

-- ========== blocks ==========
CREATE TABLE blocks (
	id INTEGER NOT NULL, 
	page_version_id INTEGER NOT NULL, 
	type VARCHAR(20) NOT NULL, 
	config_json JSON NOT NULL, 
	sort INTEGER NOT NULL, 
	mobile_visible BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(page_version_id) REFERENCES page_versions (id) ON DELETE CASCADE
);
CREATE INDEX ix_blocks_page_version_id ON blocks (page_version_id);

-- ========== collections ==========
CREATE TABLE collections (
	id INTEGER NOT NULL, 
	item_id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	year INTEGER, 
	season VARCHAR(13), 
	cover_image VARCHAR(512), 
	status VARCHAR(7) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE CASCADE
);
CREATE INDEX ix_collections_item_id ON collections (item_id);
CREATE INDEX ix_collections_status ON collections (status);

-- ========== contact_messages ==========
CREATE TABLE contact_messages (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	company VARCHAR(200), 
	contact_type VARCHAR(5) NOT NULL, 
	contact VARCHAR(200) NOT NULL, 
	coop_type VARCHAR(7), 
	content TEXT NOT NULL, 
	handle_status VARCHAR(9) NOT NULL, 
	handled_by INTEGER, 
	remark TEXT, 
	is_deleted BOOLEAN DEFAULT '0' NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_contact_messages_created_at ON contact_messages (created_at);
CREATE INDEX ix_contact_messages_handle_status ON contact_messages (handle_status);
CREATE INDEX ix_contact_messages_is_deleted ON contact_messages (is_deleted);

-- ========== items ==========
-- [记录字段] items.price：吊牌/参考零售价(元)。数据库设计文档 v1.1 / PRD v1.6 新增。
CREATE TABLE items (
	id INTEGER NOT NULL, 
	item_code VARCHAR(64) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	category VARCHAR(5) NOT NULL, 
	is_hot BOOLEAN NOT NULL, 
	hot_sort INTEGER NOT NULL, 
	images JSON, 
	video_url VARCHAR(512), 
	fabric VARCHAR(300), 
	colors JSON, 
	price NUMERIC(10, 2), 
	fit_description VARCHAR(300), 
	description TEXT, 
	sort_weight INTEGER NOT NULL, 
	status VARCHAR(7) NOT NULL, 
	ext_json JSON, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_item_cat_status ON items (category, status);
CREATE INDEX ix_item_hot ON items (is_hot, hot_sort);
CREATE INDEX ix_items_category ON items (category);
CREATE INDEX ix_items_is_hot ON items (is_hot);
CREATE UNIQUE INDEX ix_items_item_code ON items (item_code);
CREATE INDEX ix_items_status ON items (status);

-- ========== operation_logs ==========
CREATE TABLE operation_logs (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	username VARCHAR(100), 
	action_type VARCHAR(50) NOT NULL, 
	target_type VARCHAR(50) NOT NULL, 
	target_id VARCHAR(64), 
	"before" TEXT, 
	"after" TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_operation_logs_created_at ON operation_logs (created_at);
CREATE INDEX ix_operation_logs_user_id ON operation_logs (user_id);

-- ========== page_versions ==========
CREATE TABLE page_versions (
	id INTEGER NOT NULL, 
	page_id INTEGER NOT NULL, 
	version_no INTEGER NOT NULL, 
	created_by INTEGER, 
	created_at DATETIME NOT NULL, 
	note VARCHAR(200), 
	PRIMARY KEY (id), 
	FOREIGN KEY(page_id) REFERENCES pages (id) ON DELETE CASCADE
);
CREATE INDEX ix_page_versions_page_id ON page_versions (page_id);

-- ========== pages ==========
CREATE TABLE pages (
	id INTEGER NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	title VARCHAR(200) NOT NULL, 
	page_type VARCHAR(50) NOT NULL, 
	status VARCHAR(9) NOT NULL, 
	current_version_id INTEGER, 
	locked_by INTEGER, 
	locked_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE UNIQUE INDEX ix_pages_slug ON pages (slug);

-- ========== store_stocks ==========
CREATE TABLE store_stocks (
	id INTEGER NOT NULL, 
	store_id INTEGER NOT NULL, 
	item_code VARCHAR(64) NOT NULL, 
	quantity INTEGER NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_store_item UNIQUE (store_id, item_code), 
	FOREIGN KEY(store_id) REFERENCES stores (id) ON DELETE CASCADE
);
CREATE INDEX ix_store_stocks_item_code ON store_stocks (item_code);
CREATE INDEX ix_store_stocks_store_id ON store_stocks (store_id);

-- ========== stores ==========
CREATE TABLE stores (
	id INTEGER NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	province VARCHAR(50) NOT NULL, 
	city VARCHAR(50) NOT NULL, 
	district VARCHAR(50), 
	address VARCHAR(512) NOT NULL, 
	lng FLOAT NOT NULL, 
	lat FLOAT NOT NULL, 
	phone VARCHAR(50), 
	business_hours VARCHAR(200), 
	store_type VARCHAR(8) NOT NULL, 
	images JSON, 
	status VARCHAR(7) NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_stores_city ON stores (city);
CREATE INDEX ix_stores_status ON stores (status);
