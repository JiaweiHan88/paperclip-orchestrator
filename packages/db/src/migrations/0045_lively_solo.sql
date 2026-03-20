CREATE TABLE "agent_plugin_overrides" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"agent_id" uuid NOT NULL,
	"plugin_id" uuid NOT NULL,
	"enabled" boolean DEFAULT true NOT NULL,
	"tool_overrides" jsonb,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "agent_plugin_overrides" ADD CONSTRAINT "agent_plugin_overrides_agent_id_agents_id_fk" FOREIGN KEY ("agent_id") REFERENCES "public"."agents"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "agent_plugin_overrides" ADD CONSTRAINT "agent_plugin_overrides_plugin_id_plugins_id_fk" FOREIGN KEY ("plugin_id") REFERENCES "public"."plugins"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "agent_plugin_overrides_agent_idx" ON "agent_plugin_overrides" USING btree ("agent_id");--> statement-breakpoint
CREATE UNIQUE INDEX "agent_plugin_overrides_agent_plugin_uq" ON "agent_plugin_overrides" USING btree ("agent_id","plugin_id");