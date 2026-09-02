"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Shield, Sparkles, Workflow, ArrowRight } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-16">
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <Badge variant="purple">Our Mission</Badge>
        <h1 className="text-4xl font-extrabold text-slate-100">
          Building the Intelligent Flow of Digital Discourse
        </h1>
        <p className="text-xs sm:text-sm text-slate-400">
          प्रवाह (Pravah) is Sanskrit for &quot;continuous flow&quot; or &quot;stream&quot;. We build systems that automate the flow of high-signal ideas into the world.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
        <div className="space-y-4 text-xs sm:text-sm text-slate-300 leading-relaxed">
          <p>
            Modern brand growth requires continuous presence across half a dozen social platforms, each demanding tailored formats, optimal posting times, and consistent tone.
          </p>
          <p>
            Most tools are dumb queues with minimal intelligence. PRAVAH replaces fragmented scripts and manual workflows with a unified, production-grade visual automation operating system.
          </p>
          <p>
            Every line of our platform is engineered with strict multi-tenancy, cryptographic security, and deterministic reliability.
          </p>
        </div>

        <Card glow className="p-8 space-y-6 bg-slate-900/60 border-slate-800">
          <h3 className="text-lg font-bold text-slate-100">Core Engineering Principles</h3>
          <ul className="space-y-3 text-xs text-slate-300">
            <li className="flex items-start gap-2.5">
              <Shield className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
              <span><strong>Zero Compromise on Security:</strong> AES-256 Fernet encrypted tokens, Argon2 password hashing, and strict RBAC isolation.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <Workflow className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <span><strong>Visual First:</strong> Complex logic and AI chains should be understandable and editable via visual DAGs.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <Sparkles className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
              <span><strong>Deep Intelligence:</strong> AI that remembers brand identity, historical performance benchmarks, and audience intent.</span>
            </li>
          </ul>
        </Card>
      </div>

      <div className="text-center pt-8">
        <Link href="/register">
          <Button variant="glow" size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
            Join the PRAVAH Movement
          </Button>
        </Link>
      </div>
    </div>
  );
}
