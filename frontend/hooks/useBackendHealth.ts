"use client";

import { useEffect, useState } from "react";

import { fetchHealth } from "@/lib/api-client";

export function useBackendHealth() {
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    let isMounted = true;

    fetchHealth()
      .then((response) => {
        if (isMounted) {
          setStatus(response.status === "ok" ? "ok" : "error");
        }
      })
      .catch(() => {
        if (isMounted) {
          setStatus("error");
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return status;
}
