import axios from 'axios';
import {
  User,
  ManagerSubscription,
  Appointment,
  PaymentRequest,
  Site,
  Worker,
  Service,
  Detail,
  GenericResponse,
} from '../types/logic';
import { LOGIC_BASE_URL } from '../config/constants';

export class LogicAPI {
  // Users
  async getUser(id: number, token: string): Promise<User> {
    const res = await axios.get(`${LOGIC_BASE_URL}/user/${id}`, {
      headers: { Authorization: token },
    });
    return res.data;
  }
  async deleteUser(id: number, token: string): Promise<GenericResponse> {
    const res = await axios.delete(`${LOGIC_BASE_URL}/user/${id}`, {
      headers: { Authorization: token },
    });
    return { ...res.data, status: true };
  }

  // Subscription
  async updateSubscription(
    id: number,
    body: Partial<ManagerSubscription>,
    token: string,
  ): Promise<ManagerSubscription> {
    const res = await axios.put(`${LOGIC_BASE_URL}/subscription/${id}`, body, {
      headers: { Authorization: token },
    });
    return res.data.manager;
  }

  // Appointments
  async getAppointments(params: any, token: string): Promise<Appointment[]> {
    const res = await axios.get(`${LOGIC_BASE_URL}/appointment`, {
      params,
      headers: { Authorization: token },
    });
    return res.data;
  }
  async getAppointmentDetails(
    params: any,
    token: string,
  ): Promise<Appointment[]> {
    const res = await axios.get(`${LOGIC_BASE_URL}/appointmentdetail`, {
      params,
      headers: { Authorization: token },
    });
    return res.data;
  }
  async getSiteAppointmentsStatistics(
    params: any,
    token: string,
  ): Promise<any[]> {
    const res = await axios.get(
      `${LOGIC_BASE_URL}/appointment/site_statistics`,
      { params, headers: { Authorization: token } },
    );
    return res.data;
  }
  async createAppointment(body: any, token: string): Promise<GenericResponse> {
    const res = await axios.post(`${LOGIC_BASE_URL}/appointment`, body, {
      headers: { Authorization: token },
    });
    return { ...res.data, status: true };
  }
  async deleteAppointment(id: number, token: string): Promise<GenericResponse> {
    const res = await axios.delete(`${LOGIC_BASE_URL}/appointment`, {
      params: { id },
      headers: { Authorization: token },
    });
    return { ...res.data, status: true };
  }

  // Payment
  async createPayment(body: PaymentRequest, token: string): Promise<any> {
    const res = await axios.post(`${LOGIC_BASE_URL}/payment`, body, {
      headers: { Authorization: token },
    });
    return res.data;
  }

  // Sites, Workers, Services, Details...
  async getSites(params: any, token: string): Promise<Site[]> {
    const res = await axios.get(`${LOGIC_BASE_URL}/site`, {
      params,
      headers: { Authorization: token },
    });
    return res.data;
  }
  async getWorkers(params: any, token: string): Promise<Worker[]> {
    const res = await axios.get(`${LOGIC_BASE_URL}/worker`, {
      params,
      headers: { Authorization: token },
    });
    return res.data;
  }
  async getWorkerWeeklySchedule(
    worker_id: number,
    token: string,
  ): Promise<any> {
    const res = await axios.get(`${LOGIC_BASE_URL}/worker/weekly_schedule`, {
      params: { worker_id },
      headers: { Authorization: token },
    });
    return res.data;
  }
  async getServices(params: any, token: string): Promise<Service[]> {
    const res = await axios.get(`${LOGIC_BASE_URL}/service`, {
      params,
      headers: { Authorization: token },
    });
    return res.data;
  }
  async getDetails(params: any, token: string): Promise<Detail[]> {
    const res = await axios.get(`${LOGIC_BASE_URL}/detail`, {
      params,
      headers: { Authorization: token },
    });
    return res.data.map((d: any) => ({ data: d }));
  }
}
