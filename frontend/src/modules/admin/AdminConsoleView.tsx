import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { PageHeader } from "../../app/shell";
import {
  cancelPlatformJob,
  createEnvironment,
  createPlatformJob,
  createProfile,
  createProject,
  createWorkspace,
  runPlatformJob,
  useActiveContextCapabilities,
  useAuditLogs,
  useCurrentUser,
  useEnvironments,
  useFeatureFlags,
  usePlatformJobEvents,
  usePlatformJobs,
  useProfiles,
  useProjectSetupStatus,
  useProjects,
  useWorkspaces,
  upsertFeatureFlag
} from "../../platform/hooks";
import type { PlatformJobCreate } from "../../platform/types";
import {
  ActivityRow,
  ArtifactList,
  Button,
  DetailList,
  FeedbackMessage,
  MetricGrid,
  ModuleWorkspaceLayout,
  ModuleWorkspaceSide,
  OperationalPanel,
  StatePanel,
  StatusChip
} from "../../ui/components";
import { booleanStatus } from "../moduleStatus";

function firstOrNull<T extends { id: string }>(items: T[] | undefined) {
  return items?.[0]?.id ?? null;
}

function contextValue(value: string | null | undefined) {
  return value ?? "Not selected";
}

export function AdminConsoleView({ token }: { token: string }) {
  const queryClient = useQueryClient();
  const [operationMessage, setOperationMessage] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);
  const [workspaceName, setWorkspaceName] = useState("");
  const [projectWorkspaceId, setProjectWorkspaceId] = useState("");
  const [projectName, setProjectName] = useState("");
  const [profileProjectId, setProfileProjectId] = useState("");
  const [profileName, setProfileName] = useState("");
  const [environmentProjectId, setEnvironmentProjectId] = useState("");
  const [environmentType, setEnvironmentType] = useState("DEV");
  const [environmentName, setEnvironmentName] = useState("");
  const currentUser = useCurrentUser(token);
  const workspaces = useWorkspaces(token);
  const projects = useProjects(token);
  const projectId = firstOrNull(projects.data?.items);
  const profiles = useProfiles(token, projectId);
  const environments = useEnvironments(token, projectId);
  const profileId = firstOrNull(profiles.data?.items);
  const environmentId = firstOrNull(environments.data?.items);
  const setupStatus = useProjectSetupStatus(token, projectId);
  const capabilities = useActiveContextCapabilities(token);
  const jobs = usePlatformJobs(token);
  const auditLogs = useAuditLogs(token);
  const featureFlags = useFeatureFlags(token);
  const workspaceItems = workspaces.data ?? [];
  const projectItems = projects.data?.items ?? [];
  const jobItems = jobs.data?.items ?? [];
  const effectiveSelectedJobId = selectedJobId ?? jobItems[0]?.id ?? null;
  const selectedJobEvents = usePlatformJobEvents(token, effectiveSelectedJobId);
  const selectedProfileProjectId = profileProjectId || projectItems[0]?.id || "";
  const selectedEnvironmentProjectId = environmentProjectId || projectItems[0]?.id || "";
  const selectedProjectWorkspaceId = projectWorkspaceId || workspaceItems[0]?.id || "";
  const selectedProjectProfiles = useProfiles(token, selectedProfileProjectId || null);
  const selectedProjectEnvironments = useEnvironments(token, selectedEnvironmentProjectId || null);

  const refreshOperationalData = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["platform", "jobs"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "audit-logs"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "feature-flags"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "jobs", effectiveSelectedJobId, "events"] })
    ]);
  };

  const refreshSetupData = async (targetProjectId?: string | null) => {
    const setupProjectId = targetProjectId ?? projectId;
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["platform", "workspaces"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "projects"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "profiles"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "environments"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "projects", setupProjectId, "setup-status"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "project-cockpit", "summary"] })
    ]);
  };

  const handleCreateWorkspace = async () => {
    const name = workspaceName.trim();
    if (!name) {
      setOperationError("Workspace name is required.");
      return;
    }
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const workspace = await createWorkspace(token, { name });
      setWorkspaceName("");
      setProjectWorkspaceId(workspace.id);
      setOperationMessage(`Created workspace ${workspace.name}.`);
      await refreshSetupData();
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create workspace.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateProject = async () => {
    const name = projectName.trim();
    if (!name || !selectedProjectWorkspaceId) {
      setOperationError("Project name and workspace are required.");
      return;
    }
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const project = await createProject(token, { workspace_id: selectedProjectWorkspaceId, name });
      setProjectName("");
      setProfileProjectId(project.id);
      setEnvironmentProjectId(project.id);
      setOperationMessage(`Created project ${project.name}.`);
      await refreshSetupData(project.id);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create project.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateProfile = async () => {
    const name = profileName.trim();
    if (!name || !selectedProfileProjectId) {
      setOperationError("Profile name and project are required.");
      return;
    }
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const profile = await createProfile(token, { project_id: selectedProfileProjectId, name });
      setProfileName("");
      setOperationMessage(`Created profile ${profile.name}.`);
      await refreshSetupData(selectedProfileProjectId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create profile.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateEnvironment = async () => {
    const name = environmentName.trim();
    if (!name || !selectedEnvironmentProjectId) {
      setOperationError("Environment name and project are required.");
      return;
    }
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const environment = await createEnvironment(token, {
        environment_type: environmentType,
        name,
        project_id: selectedEnvironmentProjectId
      });
      setEnvironmentName("");
      setOperationMessage(`Created environment ${environment.name}.`);
      await refreshSetupData(selectedEnvironmentProjectId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create environment.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateDemoJob = async () => {
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    const payload: PlatformJobCreate = {
      job_type: "DEMO_ECHO",
      source_module: "platform",
      project_id: projectId,
      profile_id: profileId,
      environment_id: environmentId,
      domain_name: "OTM1",
      input: { value: "synthetic-admin-ui" },
      execute_now: false
    };
    try {
      const created = await createPlatformJob(token, payload);
      setSelectedJobId(created.id);
      setOperationMessage(`Created job ${created.id}.`);
      await refreshOperationalData();
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create demo job.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleRunJob = async (jobId: string) => {
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const job = await runPlatformJob(token, jobId);
      setSelectedJobId(job.id);
      setOperationMessage(job.message);
      await refreshOperationalData();
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not run job.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const job = await cancelPlatformJob(token, jobId);
      setSelectedJobId(job.id);
      setOperationMessage(job.message);
      await refreshOperationalData();
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not cancel job.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleToggleFeatureFlag = async (name: string, enabled: boolean, scope: string) => {
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const flag = await upsertFeatureFlag(token, { name, enabled, scope });
      setOperationMessage(`${flag.name} ${flag.enabled ? "enabled" : "disabled"}.`);
      await Promise.all([
        refreshOperationalData(),
        queryClient.invalidateQueries({ queryKey: ["platform", "navigation"] })
      ]);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not update feature flag.");
    } finally {
      setIsMutating(false);
    }
  };

  const isLoading =
    currentUser.isLoading ||
    workspaces.isLoading ||
    projects.isLoading ||
    capabilities.isLoading ||
    jobs.isLoading ||
    auditLogs.isLoading ||
    featureFlags.isLoading ||
    (Boolean(projectId) && setupStatus.isLoading);

  if (isLoading) {
    return <StatePanel>Loading Admin Console...</StatePanel>;
  }

  if (currentUser.isError || workspaces.isError || projects.isError || capabilities.isError || jobs.isError || auditLogs.isError) {
    return <StatePanel tone="error">Admin Console is unavailable.</StatePanel>;
  }

  const auditItems = auditLogs.data?.items ?? [];
  const featureFlagItems = featureFlags.data?.items ?? [];
  const eventItems = selectedJobEvents.data?.items ?? [];
  const capabilityItems = capabilities.data?.capabilities ?? [];
  const roleItems = capabilities.data?.roles ?? [];
  const setup = setupStatus.data;
  const canCreateDemoJob = Boolean(projectId && profileId && environmentId) && !isMutating;
  const profileAuthoringItems = selectedProjectProfiles.data?.items ?? [];
  const environmentAuthoringItems = selectedProjectEnvironments.data?.items ?? [];

  return (
    <>
      <PageHeader
        description="Platform setup, capabilities, jobs, and audit visibility for backend-owned operational contracts."
        label="Platform administration"
        title="Admin Console"
      />

      <MetricGrid
        ariaLabel="Admin Console metrics"
        items={[
          { key: "projects", label: "Projects", status: booleanStatus(projectItems.length), value: projectItems.length },
          {
            key: "capabilities",
            label: "Capabilities",
            status: booleanStatus(capabilityItems.length),
            value: capabilityItems.length
          },
          { key: "jobs", label: "Jobs", status: booleanStatus(jobItems.length), value: jobItems.length },
          { key: "audit", label: "Audit events", status: booleanStatus(auditItems.length), value: auditItems.length }
        ]}
      />

      {operationMessage ? <FeedbackMessage tone="success">{operationMessage}</FeedbackMessage> : null}
      {operationError ? <FeedbackMessage tone="error">{operationError}</FeedbackMessage> : null}

      <ModuleWorkspaceLayout
        ariaLabel="Platform jobs"
        side={
          <ModuleWorkspaceSide ariaLabel="Admin setup and capability details" title="Setup and access">
            <OperationalPanel
              ariaLabel="Setup authoring"
              emptyText="No setup entities available."
              hasItems={workspaceItems.length > 0 || projectItems.length > 0}
              status={projectItems.length ? "ACTIVE" : "EMPTY"}
              title="Setup authoring"
            >
              <div className="admin-setup-authoring">
                <form
                  className="admin-setup-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreateWorkspace();
                  }}
                >
                  <label>
                    Workspace name
                    <input
                      onChange={(event) => setWorkspaceName(event.target.value)}
                      placeholder="Synthetic workspace"
                      value={workspaceName}
                    />
                  </label>
                  <Button disabled={isMutating} type="submit" variant="primary">
                    Create workspace
                  </Button>
                  <div className="admin-setup-list">
                    {workspaceItems.slice(-3).map((workspace) => (
                      <span key={workspace.id}>{workspace.name}</span>
                    ))}
                  </div>
                </form>

                <form
                  className="admin-setup-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreateProject();
                  }}
                >
                  <label>
                    Project workspace
                    <select onChange={(event) => setProjectWorkspaceId(event.target.value)} value={selectedProjectWorkspaceId}>
                      {workspaceItems.map((workspace) => (
                        <option key={workspace.id} value={workspace.id}>
                          {workspace.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Project name
                    <input onChange={(event) => setProjectName(event.target.value)} placeholder="Synthetic project" value={projectName} />
                  </label>
                  <Button disabled={isMutating || !workspaceItems.length} type="submit" variant="primary">
                    Create project
                  </Button>
                  <div className="admin-setup-list">
                    {projectItems.slice(-3).map((project) => (
                      <span key={project.id}>{project.name}</span>
                    ))}
                  </div>
                </form>

                <form
                  className="admin-setup-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreateProfile();
                  }}
                >
                  <label>
                    Profile project
                    <select onChange={(event) => setProfileProjectId(event.target.value)} value={selectedProfileProjectId}>
                      {projectItems.map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Profile name
                    <input onChange={(event) => setProfileName(event.target.value)} placeholder="Default profile" value={profileName} />
                  </label>
                  <Button disabled={isMutating || !projectItems.length} type="submit" variant="primary">
                    Create profile
                  </Button>
                  <div className="admin-setup-list">
                    {profileAuthoringItems.slice(-3).map((profile) => (
                      <span key={profile.id}>{profile.name}</span>
                    ))}
                  </div>
                </form>

                <form
                  className="admin-setup-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreateEnvironment();
                  }}
                >
                  <label>
                    Environment project
                    <select onChange={(event) => setEnvironmentProjectId(event.target.value)} value={selectedEnvironmentProjectId}>
                      {projectItems.map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Environment type
                    <select onChange={(event) => setEnvironmentType(event.target.value)} value={environmentType}>
                      <option value="DEV">DEV</option>
                      <option value="TEST">TEST</option>
                      <option value="UAT">UAT</option>
                      <option value="PROD">PROD</option>
                    </select>
                  </label>
                  <label>
                    Environment name
                    <input
                      onChange={(event) => setEnvironmentName(event.target.value)}
                      placeholder="DEV environment"
                      value={environmentName}
                    />
                  </label>
                  <Button disabled={isMutating || !projectItems.length} type="submit" variant="primary">
                    Create environment
                  </Button>
                  <div className="admin-setup-list">
                    {environmentAuthoringItems.slice(-3).map((environment) => (
                      <span key={environment.id}>{environment.name}</span>
                    ))}
                  </div>
                </form>
              </div>
            </OperationalPanel>

            <DetailList
              ariaLabel="Project setup status"
              emptyText="No project setup status available."
              items={
                setup
                  ? [
                      {
                        id: setup.project_id,
                        meta: [
                          `Profiles ${setup.profile_count}`,
                          `Environments ${setup.environment_count}`,
                          setup.active_context_selected ? "Active context selected" : "Active context missing"
                        ],
                        status: setup.status,
                        title: setup.project_name
                      }
                    ]
                  : []
              }
            />

            <OperationalPanel
              ariaLabel="Effective capabilities"
              emptyText="No effective capabilities for this context."
              hasItems={capabilityItems.length > 0 || roleItems.length > 0}
              status={capabilityItems.length ? "ACTIVE" : "EMPTY"}
              title="Effective capabilities"
            >
              <ActivityRow
                status={capabilities.data?.is_admin ? "ADMIN" : "SCOPED"}
                subtitle={currentUser.data?.email ?? "Unknown user"}
                title={capabilityItems.join(", ")}
              />
              {roleItems.map((role) => (
                <ActivityRow key={role} status="ROLE" subtitle={contextValue(capabilities.data?.project_id)} title={role} />
              ))}
            </OperationalPanel>

            <OperationalPanel
              ariaLabel="Selected job events"
              emptyText="Select a job to inspect lifecycle events."
              hasItems={eventItems.length > 0}
              isLoading={selectedJobEvents.isLoading && Boolean(effectiveSelectedJobId)}
              loadingText="Loading selected job events..."
              status={eventItems.length ? "ACTIVE" : "EMPTY"}
              title="Selected job events"
            >
              {eventItems.map((event) => (
                <ActivityRow
                  key={event.id}
                  status={event.status_after ?? event.event_type}
                  subtitle={event.message}
                  title={event.event_type}
                />
              ))}
            </OperationalPanel>

            <OperationalPanel
              ariaLabel="Feature flags"
              emptyText="No feature flags configured."
              hasItems={featureFlagItems.length > 0}
              status={featureFlagItems.length ? "ACTIVE" : "EMPTY"}
              title="Feature flags"
            >
              <div className="admin-feature-flags">
                {featureFlagItems.map((flag) => (
                  <div className="admin-feature-flag-row" key={flag.id}>
                    <div>
                      <strong>{flag.name}</strong>
                      <span>{flag.scope}</span>
                    </div>
                    <StatusChip status={flag.enabled ? "ENABLED" : "DISABLED"} />
                    <Button
                      aria-label={`${flag.enabled ? "Disable" : "Enable"} feature flag ${flag.name}`}
                      disabled={isMutating}
                      onClick={() => handleToggleFeatureFlag(flag.name, !flag.enabled, flag.scope)}
                      variant={flag.enabled ? "secondary" : "primary"}
                    >
                      {flag.enabled ? "Disable" : "Enable"}
                    </Button>
                  </div>
                ))}
              </div>
            </OperationalPanel>

            <OperationalPanel
              ariaLabel="Audit trail"
              emptyText="No audit events recorded."
              hasItems={auditItems.length > 0}
              status={auditItems.length ? "ACTIVE" : "EMPTY"}
              title="Audit trail"
            >
              {auditItems.slice(0, 8).map((item) => (
                <ActivityRow key={item.id} status={item.target_type} subtitle={item.target_id} title={item.action} />
              ))}
            </OperationalPanel>
          </ModuleWorkspaceSide>
        }
        status={jobItems.length ? "ACTIVE" : "EMPTY"}
        title="Platform jobs"
      >
        <div className="admin-console-actions">
          <Button disabled={!canCreateDemoJob} onClick={handleCreateDemoJob} variant="primary">
            Create demo job
          </Button>
          <span>
            {projectItems[0]?.name ?? "No project"} / {profiles.data?.items[0]?.name ?? "No profile"} /{" "}
            {environments.data?.items[0]?.name ?? "No environment"}
          </span>
        </div>

        <ArtifactList
          items={jobItems.map((job) => ({
            id: job.id,
            meta: [job.job_type, job.source_module, `${job.progress}%`],
            status: job.status,
            subtitle: job.message,
            title: job.id,
            action: (
              <div className="admin-job-actions">
                <Button aria-label={`View events ${job.id}`} disabled={isMutating} onClick={() => setSelectedJobId(job.id)}>
                  View
                </Button>
                {job.status === "PENDING" ? (
                  <>
                    <Button aria-label={`Run job ${job.id}`} disabled={isMutating} onClick={() => handleRunJob(job.id)} variant="primary">
                      Run
                    </Button>
                    <Button aria-label={`Cancel job ${job.id}`} disabled={isMutating} onClick={() => handleCancelJob(job.id)}>
                      Cancel
                    </Button>
                  </>
                ) : (
                  <StatusChip status={job.status} />
                )}
              </div>
            )
          }))}
        />
      </ModuleWorkspaceLayout>
    </>
  );
}
