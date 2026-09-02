"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { fetchApi } from "@/lib/api";
import { useAuth } from "./auth-provider";
import { Organisation } from "@pravah/shared-types";

interface OrgContextType {
  organisations: Organisation[];
  activeOrg: Organisation | null;
  isLoading: boolean;
  switchOrganisation: (orgId: string) => void;
  refreshOrganisations: () => Promise<void>;
}

const OrgContext = createContext<OrgContextType | undefined>(undefined);

export function OrgProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [organisations, setOrganisations] = useState<Organisation[]>([]);
  const [activeOrg, setActiveOrg] = useState<Organisation | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchOrganisations = async () => {
    if (!isAuthenticated) {
      setOrganisations([]);
      setActiveOrg(null);
      setIsLoading(false);
      return;
    }

    try {
      const orgs = await fetchApi<Organisation[]>("/organisations");
      setOrganisations(orgs);

      const savedOrgId = localStorage.getItem("pravah_active_org_id");
      const matched = orgs.find((o) => o.id === savedOrgId) || orgs[0] || null;

      if (matched) {
        setActiveOrg(matched);
        localStorage.setItem("pravah_active_org_id", matched.id);
      }
    } catch {
      setOrganisations([]);
      setActiveOrg(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOrganisations();
  }, [isAuthenticated]);

  const switchOrganisation = (orgId: string) => {
    const target = organisations.find((o) => o.id === orgId);
    if (target) {
      setActiveOrg(target);
      localStorage.setItem("pravah_active_org_id", target.id);
      window.location.reload();
    }
  };

  return (
    <OrgContext.Provider
      value={{
        organisations,
        activeOrg,
        isLoading,
        switchOrganisation,
        refreshOrganisations: fetchOrganisations,
      }}
    >
      {children}
    </OrgContext.Provider>
  );
}

export function useOrganisation() {
  const context = useContext(OrgContext);
  if (!context) {
    throw new Error("useOrganisation must be used within an OrgProvider");
  }
  return context;
}
