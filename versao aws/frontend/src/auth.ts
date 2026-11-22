// Login com o Cognito, pelas funções do Amplify (só a parte de autenticação).
//
// Sem as variáveis VITE_COGNITO_*, o login fica desligado: é o modo de
// desenvolvimento, em que a API também roda sem login (AUTH_DISABLED).

import { Amplify } from "aws-amplify";
import {
  confirmResetPassword,
  confirmSignUp,
  fetchAuthSession,
  getCurrentUser,
  resendSignUpCode,
  resetPassword,
  signIn,
  signOut,
  signUp,
} from "aws-amplify/auth";

const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID as string | undefined;
const userPoolClientId = import.meta.env.VITE_COGNITO_CLIENT_ID as string | undefined;

export const authEnabled = Boolean(userPoolId && userPoolClientId);

if (authEnabled) {
  Amplify.configure({
    Auth: { Cognito: { userPoolId: userPoolId!, userPoolClientId: userPoolClientId!, loginWith: { email: true } } },
  });
}

/** Token de acesso para mandar à API, ou null sem login. Renova sozinho quando vence. */
export async function accessToken(): Promise<string | null> {
  if (!authEnabled) return null;
  const session = await fetchAuthSession();
  return session.tokens?.accessToken?.toString() ?? null;
}

export async function isSignedIn(): Promise<boolean> {
  if (!authEnabled) return true;
  try {
    await getCurrentUser();
    return true;
  } catch {
    return false;
  }
}

export async function login(email: string, password: string): Promise<"done" | "confirm"> {
  const { nextStep } = await signIn({ username: email, password });
  if (nextStep.signInStep === "CONFIRM_SIGN_UP") return "confirm";
  return "done";
}

export async function register(email: string, password: string): Promise<void> {
  await signUp({ username: email, password, options: { userAttributes: { email } } });
}

export async function confirmCode(email: string, code: string): Promise<void> {
  await confirmSignUp({ username: email, confirmationCode: code });
}

export async function resendCode(email: string): Promise<void> {
  await resendSignUpCode({ username: email });
}

export async function forgotPassword(email: string): Promise<void> {
  await resetPassword({ username: email });
}

export async function newPassword(email: string, code: string, password: string): Promise<void> {
  await confirmResetPassword({ username: email, confirmationCode: code, newPassword: password });
}

export async function logout(): Promise<void> {
  if (authEnabled) await signOut();
}

/** Mensagens do Cognito em português, para os erros mais comuns. */
export function authMessage(e: unknown): string {
  const name = (e as { name?: string })?.name ?? "";
  const message = (e as { message?: string })?.message ?? "";
  const known: Record<string, string> = {
    NotAuthorizedException: "E-mail ou senha incorretos.",
    UserNotFoundException: "E-mail ou senha incorretos.",
    UsernameExistsException: "Já existe uma conta com esse e-mail.",
    CodeMismatchException: "Código incorreto. Confira o e-mail e tente de novo.",
    ExpiredCodeException: "O código expirou. Peça um novo.",
    InvalidPasswordException:
      "A senha precisa ter pelo menos 8 caracteres, com letra maiúscula, minúscula, número e símbolo.",
    LimitExceededException: "Muitas tentativas. Espere alguns minutos e tente de novo.",
    InvalidParameterException: "Confira o e-mail e a senha informados.",
  };
  // Recusa do gatilho de cadastro (teto do mês atingido): o texto vem do backend.
  if (name === "UserLambdaValidationException") return message.replace(/^PreSignUp failed with error /, "");
  return known[name] ?? "Não foi possível concluir. Tente de novo.";
}
