import { LogicAPI } from '../../datasources/logicAPI';
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
} from '../../types/logic';

// Define context interface that contains token
interface Context {
  token: string;
}

const logicAPI = new LogicAPI();

export const logicResolvers = {
  Query: {
    getUser: (
      _: unknown,
      { id }: { id: number },
      { token }: Context,
    ): Promise<User> => logicAPI.getUser(id, token),

    deleteUser: (
      _: unknown,
      { id }: { id: number },
      { token }: Context,
    ): Promise<GenericResponse> => logicAPI.deleteUser(id, token),

    getAppointments: (
      _: unknown,
      args: Record<string, any>,
      { token }: Context,
    ): Promise<Appointment[]> => logicAPI.getAppointments(args, token),

    getAppointmentDetails: (
      _: unknown,
      args: Record<string, any>,
      { token }: Context,
    ): Promise<Detail> => logicAPI.getAppointmentDetails(args, token),

    getSiteAppointmentsStatistics: (
      _: unknown,
      args: Record<string, any>,
      { token }: Context,
    ): Promise<Detail> => logicAPI.getSiteAppointmentsStatistics(args, token),

    getSites: (
      _: unknown,
      args: Record<string, any>,
      { token }: Context,
    ): Promise<Site[]> => logicAPI.getSites(args, token),

    getWorkers: (
      _: unknown,
      args: Record<string, any>,
      { token }: Context,
    ): Promise<Worker[]> => logicAPI.getWorkers(args, token),

    getWorkerWeeklySchedule: (
      _: unknown,
      { worker_id }: { worker_id: number },
      { token }: Context,
    ): Promise<Detail> => logicAPI.getWorkerWeeklySchedule(worker_id, token),

    getServices: (
      _: unknown,
      args: Record<string, any>,
      { token }: Context,
    ): Promise<Service[]> => logicAPI.getServices(args, token),

    getDetails: (
      _: unknown,
      args: Record<string, any>,
      { token }: Context,
    ): Promise<Detail> => logicAPI.getDetails(args, token),
  },

  Mutation: {
    updateSubscription: (
      _: unknown,
      args: { id: number } & Partial<ManagerSubscription>,
      { token }: Context,
    ): Promise<ManagerSubscription> =>
      logicAPI.updateSubscription(args.id, args, token),

    createAppointment: (
      _: unknown,
      { input }: { input: Partial<Appointment> },
      { token }: Context,
    ): Promise<GenericResponse> => logicAPI.createAppointment(input, token),

    deleteAppointment: (
      _: unknown,
      { id }: { id: number },
      { token }: Context,
    ): Promise<GenericResponse> => logicAPI.deleteAppointment(id, token),

    createPayment: (
      _: unknown,
      { input }: { input: PaymentRequest },
      { token }: Context,
    ): Promise<GenericResponse> => logicAPI.createPayment(input, token),
  },
};
