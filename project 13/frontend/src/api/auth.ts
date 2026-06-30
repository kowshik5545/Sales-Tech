import axios from "axios";

export interface User {
  id: string;
  email: string;
  name: string;
  role: "admin" | "manager" | "rep";
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface CreateUserRequest {
  email: string;
  password: string;
  name: string;
  role: string;
}

export interface UpdateUserRequest {
  name?: string;
  role?: string;
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "/api";

const authClient = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000,
});

function authHeaders(token: string) {
  return { headers: { Authorization: `Bearer ${token}` } };
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await authClient.post<LoginResponse>("/auth/login", { email, password });
  return data;
}

export async function getMe(token: string): Promise<User> {
  const { data } = await authClient.get<User>("/auth/me", authHeaders(token));
  return data;
}

export async function getUsers(token: string): Promise<User[]> {
  const { data } = await authClient.get<User[]>("/auth/users", authHeaders(token));
  return data;
}

export async function createUser(token: string, req: CreateUserRequest): Promise<User> {
  const { data } = await authClient.post<User>("/auth/users", req, authHeaders(token));
  return data;
}

export async function updateUser(token: string, userId: string, req: UpdateUserRequest): Promise<User> {
  const { data } = await authClient.patch<User>(`/auth/users/${userId}`, req, authHeaders(token));
  return data;
}

export async function deleteUser(token: string, userId: string): Promise<void> {
  await authClient.delete(`/auth/users/${userId}`, authHeaders(token));
}
