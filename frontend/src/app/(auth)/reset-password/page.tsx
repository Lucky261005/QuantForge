"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2 } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useResetPassword } from "@/hooks/use-auth";
import { getApiErrorMessage } from "@/lib/api-client";

const schema = z
  .object({
    password: z.string().min(8, "Use at least 8 characters").max(128),
    confirm: z.string(),
  })
  .refine((v) => v.password === v.confirm, { message: "Passwords don't match", path: ["confirm"] });
type FormValues = z.infer<typeof schema>;

const linkClass = "font-medium text-primary underline decoration-primary/40 underline-offset-4 hover:decoration-primary";

function ResetPasswordForm() {
  const token = useSearchParams().get("token");
  const resetPassword = useResetPassword();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  if (!token) {
    return (
      <div>
        <h1 className="display text-3xl">Link is incomplete</h1>
        <p className="mt-4 text-sm text-muted-foreground">
          This reset link is missing its token. Open the link from the email again, or{" "}
          <Link href="/forgot-password" className={linkClass}>
            request a new one
          </Link>
          .
        </p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="display text-3xl">Choose a new password</h1>
      <p className="mt-4 text-sm text-muted-foreground">The link works once and expires 30 minutes after it was sent.</p>

      <form
        className="mt-6 space-y-4"
        onSubmit={handleSubmit((v) => resetPassword.mutate({ token, new_password: v.password }))}
      >
        <div className="space-y-2">
          <Label htmlFor="password">New password</Label>
          <Input id="password" type="password" autoComplete="new-password" {...register("password")} />
          {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
        </div>
        <div className="space-y-2">
          <Label htmlFor="confirm">Confirm new password</Label>
          <Input id="confirm" type="password" autoComplete="new-password" {...register("confirm")} />
          {errors.confirm && <p className="text-xs text-destructive">{errors.confirm.message}</p>}
        </div>

        {resetPassword.isError && (
          <p role="alert" className="text-sm text-destructive">
            {getApiErrorMessage(resetPassword.error)}. This link may have expired or already been used.{" "}
            <Link href="/forgot-password" className={linkClass}>
              Request a new link
            </Link>
            .
          </p>
        )}

        <Button type="submit" variant="gradient" className="w-full" disabled={resetPassword.isPending}>
          {resetPassword.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          Set new password
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        <Link href="/login" className={linkClass}>
          Back to login
        </Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  // useSearchParams needs a Suspense boundary for static rendering.
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  );
}
