import { AuthAPI } from '../../datasources/authAPI';
import {
  LoginRequest,
  RegisterUserRequest,
  RegisterManagerRequest,
} from '../../types/auth';

const authAPI = new AuthAPI();

export const authResolvers = {
  Mutation: {
    login: async (_: any, args: LoginRequest) => {
      return await authAPI.login(args);
    },
    registerUser: async (_: any, args: RegisterUserRequest) => {
      return await authAPI.registerUser(args);
    },
    registerManager: async (_: any, args: RegisterManagerRequest) => {
      return await authAPI.registerManager(args);
    },
  },
};
