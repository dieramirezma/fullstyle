-- Frozen phase-5 schema. Add changes in a new migration.
CREATE TABLE cache_epoch (
	namespace VARCHAR(40) NOT NULL, 
	generation VARCHAR(32) NOT NULL, 
	PRIMARY KEY (namespace)
);

CREATE TABLE category (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

CREATE TABLE client (
	id SERIAL NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE mail_event (
	id VARCHAR(64) NOT NULL, 
	payload JSON NOT NULL, 
	payload_hash VARCHAR(64) NOT NULL, 
	state VARCHAR(20) DEFAULT 'pending' NOT NULL, 
	attempts INTEGER DEFAULT '0' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	next_attempt TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	delivered_at TIMESTAMP WITH TIME ZONE, 
	last_error VARCHAR(80), 
	PRIMARY KEY (id)
);

CREATE TABLE provider_receipt (
	id VARCHAR(36) NOT NULL, 
	provider VARCHAR(30) NOT NULL, 
	transaction_id VARCHAR(150) NOT NULL, 
	payload JSON NOT NULL, 
	state VARCHAR(30) NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE session_revocation (
	subject VARCHAR(100) NOT NULL, 
	token_type VARCHAR(20) NOT NULL, 
	jti VARCHAR(100) NOT NULL, 
	expires_at BIGINT NOT NULL, 
	PRIMARY KEY (subject, token_type, jti)
);

CREATE TABLE site (
	id SERIAL NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	address VARCHAR(255) NOT NULL, 
	phone VARCHAR(20), 
	manager_id INTEGER NOT NULL, 
	photos JSON, 
	PRIMARY KEY (id)
);

CREATE TABLE userr (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	email VARCHAR(150) NOT NULL, 
	password VARCHAR(255), 
	active BOOLEAN NOT NULL, 
	auth_provider VARCHAR(20) NOT NULL, 
	google_id VARCHAR(100), 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	UNIQUE (google_id)
);

CREATE TABLE chat_turn (
	sequence BIGSERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	session_id VARCHAR(120) NOT NULL, 
	operation_id VARCHAR(80) NOT NULL, 
	message TEXT NOT NULL, 
	reply TEXT, 
	state VARCHAR(20) DEFAULT 'pending' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (sequence), 
	UNIQUE (user_id, session_id, operation_id), 
	FOREIGN KEY(user_id) REFERENCES userr (id) ON DELETE CASCADE
);

CREATE TABLE identity_link (
	provider VARCHAR(30) NOT NULL, 
	subject VARCHAR(150) NOT NULL, 
	user_id INTEGER NOT NULL, 
	PRIMARY KEY (provider, subject), 
	UNIQUE (provider, user_id), 
	FOREIGN KEY(user_id) REFERENCES userr (id)
);

CREATE TABLE mail_delivery (
	event_id VARCHAR(64) NOT NULL, 
	ordinal INTEGER NOT NULL, 
	result JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (event_id, ordinal), 
	FOREIGN KEY(event_id) REFERENCES mail_event (id) ON DELETE CASCADE
);

CREATE TABLE manager (
	id INTEGER NOT NULL, 
	bankaccount BIGINT NOT NULL, 
	accounttype VARCHAR(45) NOT NULL, 
	bankentity VARCHAR(45) NOT NULL, 
	subscriptionactive BOOLEAN NOT NULL, 
	subscriptionstartdate TIMESTAMP WITH TIME ZONE, 
	subscriptiontype VARCHAR(45), 
	subscriptionfinishdate TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id) REFERENCES userr (id)
);

CREATE TABLE service (
	id SERIAL NOT NULL, 
	category_id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES category (id)
);

CREATE TABLE site_has_category (
	site_id INTEGER NOT NULL, 
	category_id INTEGER NOT NULL, 
	PRIMARY KEY (site_id, category_id), 
	FOREIGN KEY(site_id) REFERENCES site (id) ON DELETE CASCADE, 
	FOREIGN KEY(category_id) REFERENCES category (id) ON DELETE CASCADE
);

CREATE TABLE worker (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	site_id INTEGER NOT NULL, 
	profilepicture VARCHAR(255), 
	description TEXT, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(site_id) REFERENCES site (id) ON DELETE CASCADE
);

CREATE TABLE appointment (
	id SERIAL NOT NULL, 
	appointmenttime TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	worker_id INTEGER NOT NULL, 
	site_id INTEGER NOT NULL, 
	service_id INTEGER NOT NULL, 
	client_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(worker_id) REFERENCES worker (id) ON DELETE CASCADE, 
	FOREIGN KEY(site_id) REFERENCES site (id) ON DELETE CASCADE, 
	FOREIGN KEY(service_id) REFERENCES service (id) ON DELETE CASCADE
);

CREATE TABLE availability (
	id SERIAL NOT NULL, 
	worker_id INTEGER NOT NULL, 
	weekday VARCHAR(10) NOT NULL, 
	starttime TIME WITHOUT TIME ZONE NOT NULL, 
	endtime TIME WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(worker_id) REFERENCES worker (id) ON DELETE CASCADE
);

CREATE TABLE days_off (
	id SERIAL NOT NULL, 
	worker_id INTEGER NOT NULL, 
	dayoff DATE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(worker_id) REFERENCES worker (id) ON DELETE CASCADE
);

CREATE TABLE detail (
	site_id INTEGER NOT NULL, 
	service_id INTEGER NOT NULL, 
	description TEXT, 
	price INTEGER NOT NULL, 
	duration INTEGER NOT NULL, 
	photos JSON, 
	active BOOLEAN NOT NULL, 
	PRIMARY KEY (site_id, service_id), 
	FOREIGN KEY(site_id) REFERENCES site (id) ON DELETE CASCADE, 
	FOREIGN KEY(service_id) REFERENCES service (id) ON DELETE CASCADE
);

CREATE TABLE seasonal_schedule (
	id SERIAL NOT NULL, 
	worker_id INTEGER NOT NULL, 
	seasonname VARCHAR(50) NOT NULL, 
	startdate DATE NOT NULL, 
	enddate DATE NOT NULL, 
	starttime TIME WITHOUT TIME ZONE NOT NULL, 
	endtime TIME WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(worker_id) REFERENCES worker (id) ON DELETE CASCADE
);

CREATE TABLE worker_has_service (
	worker_id INTEGER NOT NULL, 
	service_id INTEGER NOT NULL, 
	PRIMARY KEY (worker_id, service_id), 
	FOREIGN KEY(worker_id) REFERENCES worker (id) ON DELETE CASCADE, 
	FOREIGN KEY(service_id) REFERENCES service (id) ON DELETE CASCADE
);

CREATE TABLE booking_terms (
	appointment_id INTEGER NOT NULL, 
	duration INTEGER NOT NULL, 
	amount INTEGER NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	PRIMARY KEY (appointment_id), 
	CONSTRAINT valid_booking_terms CHECK (duration > 0 AND amount >= 0), 
	FOREIGN KEY(appointment_id) REFERENCES appointment (id) ON DELETE CASCADE
);

CREATE TABLE notification (
	id SERIAL NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	type VARCHAR(50) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	appointment_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(appointment_id) REFERENCES appointment (id) ON DELETE CASCADE
);

CREATE TABLE payment (
	id SERIAL NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	amount INTEGER NOT NULL, 
	paymentmethod VARCHAR(50) NOT NULL, 
	status VARCHAR(50) NOT NULL, 
	appointment_id INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(appointment_id) REFERENCES appointment (id) ON DELETE CASCADE
);

CREATE TABLE payment_intent (
	reference VARCHAR(36) NOT NULL, 
	appointment_id INTEGER NOT NULL, 
	payment_id INTEGER NOT NULL, 
	amount_in_cents BIGINT NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	PRIMARY KEY (reference), 
	CONSTRAINT positive_payment_intent CHECK (amount_in_cents > 0), 
	UNIQUE (appointment_id), 
	FOREIGN KEY(appointment_id) REFERENCES appointment (id) ON DELETE CASCADE, 
	UNIQUE (payment_id), 
	FOREIGN KEY(payment_id) REFERENCES payment (id) ON DELETE RESTRICT
);

CREATE TABLE provider_transaction (
	provider VARCHAR(30) NOT NULL, 
	transaction_id VARCHAR(150) NOT NULL, 
	receipt_id VARCHAR(36) NOT NULL, 
	reference VARCHAR(150), 
	amount_in_cents BIGINT, 
	currency VARCHAR(3), 
	status VARCHAR(30) NOT NULL, 
	verified_payload JSON NOT NULL, 
	applied_payment_id INTEGER, 
	PRIMARY KEY (provider, transaction_id), 
	UNIQUE (receipt_id), 
	FOREIGN KEY(receipt_id) REFERENCES provider_receipt (id) ON DELETE CASCADE, 
	UNIQUE (applied_payment_id), 
	FOREIGN KEY(applied_payment_id) REFERENCES payment (id)
);

CREATE INDEX ix_mail_event_next_attempt ON mail_event (next_attempt);

CREATE INDEX ix_mail_event_state ON mail_event (state);

CREATE INDEX ix_chat_history ON chat_turn (user_id, session_id, sequence);
