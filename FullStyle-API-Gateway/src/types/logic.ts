// Users
export interface User {
  id: number;
  name: string;
  email: string;
  active: boolean;
}

// Subscription update response
export interface ManagerSubscription {
  id: number;
  subscriptionactive: boolean;
  subscriptionstartdate: string;
  subscriptiontype: string;
  subscriptionfinishdate: string;
}

// Appointment
export interface Appointment {
  id: number;
  appointmenttime: string;
  status?: string;
  worker_id?: number;
  site_id?: number;
  service_id?: number;
  client_id?: number;
}

// Payment
export interface PaymentRequest {
  amount?: number;
  paymentmethod?: string;
  status?: string;
  appointment_id?: number;
}

// Site, Worker, Service, Detail definitions
export interface Site {
  id: number;
  name: string;
  address: string;
  phone: number;
  manager_id: number;
}
export interface Worker {
  id: number;
  user_id: number;
  site_id: number;
}
export interface Service {
  id: number;
  name: string;
  category_id: number;
}

// Detail is generic object
export type Detail = Record<string, any>;

// Generic Response
export interface GenericResponse {
  message: string;
}
