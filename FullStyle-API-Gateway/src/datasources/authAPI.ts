import axios from 'axios';
import {
  LoginRequest,
  RegisterUserRequest,
  RegisterManagerRequest,
  LoginResponse,
  RegisterUserResponse,
} from '../types/auth';
import { AUTH_BASE_URL } from '../config/constants';

export class AuthAPI {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const res = await axios.post(`${AUTH_BASE_URL}/login`, credentials, {
        timeout: 8000,
      });
      return res.data;
    } catch (error: any) {
      console.log('URL: ', `${AUTH_BASE_URL}/login`);
      console.error('Login error:', error.response?.data || error.message);
      throw new Error(error.response?.data?.error || 'Login failed');
    }
  }

  async registerUser(user: RegisterUserRequest): Promise<RegisterUserResponse> {
    try {
      const res = await axios.post(`${AUTH_BASE_URL}/register`, user, {
        timeout: 8000,
      });
      return {
        message: res.data.message || 'Usuario registrado',
        user: res.data.user,
      };
    } catch (error: any) {
      console.error(
        'Register user error:',
        error.response?.data || error.message,
      );
      throw new Error(error.response?.data?.error || 'Register failed');
    }
  }

  async registerManager(
    manager: RegisterManagerRequest,
  ): Promise<RegisterUserResponse> {
    try {
      const res = await axios.post(
        `${AUTH_BASE_URL}/manager_register`,
        manager,
        { timeout: 8000 },
      );
      return {
        message: res.data.message || 'Manager registrado',
        user: res.data.user,
      };
    } catch (error: any) {
      console.error(
        'Register manager error:',
        error.response?.data || error.message,
      );
      throw new Error(error.response?.data?.error || 'Register failed');
    }
  }
}
