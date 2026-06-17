import { Suspense } from "react";

import LoginForm from "./LoginForm";

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="text-center text-sm text-slate-600">Loading sign in...</div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
