export interface LoginRequest {
  otp?: string;
  email: string;
  password: string;
}

export interface RegisterUserRequest {
  name: string;
  email: string;
  password: string;
}

export interface RegisterManagerRequest extends RegisterUserRequest {
  bankaccount: number;
  bankentity: string;
  accounttype: string;
  subscriptionactive: boolean;
  subscriptionstartdate: string;
  subscriptionfinishdate: string;
  subscriptiontype: string;
}

export interface User {
  id: number;
  name: string;
  email: string;
  active: boolean;
}

export interface LoginResponse {
  message: string;
  token: string;
  refresh_token?: string;
  user: User;
}

export interface RegisterUserResponse {
  message: string;
  user: User;
}
