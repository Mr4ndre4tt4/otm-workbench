export function ContextSummary({ context }: { context: Record<string, unknown> }) {
  const projectId = context.project_id as string | null;
  const profileId = context.profile_id as string | null;
  const environmentId = context.environment_id as string | null;
  const domainName = context.domain_name as string | null;
  return (
    <div className="context-summary" aria-label="Active context">
      <span>{projectId ? "Project selected" : "No project selected"}</span>
      <span>{profileId ? "Profile selected" : "Profile pending"}</span>
      <span>{environmentId ? "Environment selected" : "Environment pending"}</span>
      <span>{domainName ?? "PUBLIC"}</span>
    </div>
  );
}
