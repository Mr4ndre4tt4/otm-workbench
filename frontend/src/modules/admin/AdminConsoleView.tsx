import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { PageHeader } from "../../app/shell";
import {
  cancelPlatformJob,
  createAccessPolicy,
  createEnvironment,
  createGrant,
  createPlatformJob,
  createProfile,
  createProject,
  createRole,
  createUser,
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
  useSettingsAccessModel,
  useSettingsScopeAuthority,
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
  const [roleName, setRoleName] = useState("");
  const [roleCapabilityNames, setRoleCapabilityNames] = useState("");
  const [userEmail, setUserEmail] = useState("");
  const [userPassword, setUserPassword] = useState("SyntheticPass123!");
  const [grantProjectId, setGrantProjectId] = useState("");
  const [grantEnvironmentId, setGrantEnvironmentId] = useState("");
  const [grantDomainName, setGrantDomainName] = useState("");
  const [grantUserId, setGrantUserId] = useState("");
  const [grantRoleId, setGrantRoleId] = useState("");
  const [accessPolicyProjectId, setAccessPolicyProjectId] = useState("");
  const [accessPolicyName, setAccessPolicyName] = useState("");
  const [accessPolicyVisibility, setAccessPolicyVisibility] = useState("PRIVATE");
  const [accessPolicyDomainName, setAccessPolicyDomainName] = useState("");
  const [accessPolicyRuleJson, setAccessPolicyRuleJson] = useState("{\"mode\":\"domain_role\"}");
  const currentUser = useCurrentUser(token);
  const workspaces = useWorkspaces(token);
  const projects = useProjects(token);
  const projectId = firstOrNull(projects.data?.items);
  const profiles = useProfiles(token, projectId);
  const environments = useEnvironments(token, projectId);
  const profileId = firstOrNull(profiles.data?.items);
  const environmentId = firstOrNull(environments.data?.items);
  const setupStatus = useProjectSetupStatus(token, projectId);
  const scopeAuthority = useSettingsScopeAuthority(token);
  const accessModel = useSettingsAccessModel(token);
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
  const selectedGrantProjectEnvironments = useEnvironments(token, grantProjectId || projectId);

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
      queryClient.invalidateQueries({ queryKey: ["platform", "settings", "scope-authority"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "settings", "access-model"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "projects", setupProjectId, "setup-status"] }),
      queryClient.invalidateQueries({ queryKey: ["platform", "project-cockpit", "summary"] })
    ]);
  };

  const resetSetupDrafts = () => {
    setWorkspaceName("");
    setProjectWorkspaceId("");
    setProjectName("");
    setProfileProjectId("");
    setProfileName("");
    setEnvironmentProjectId("");
    setEnvironmentType("DEV");
    setEnvironmentName("");
    setRoleName("");
    setRoleCapabilityNames("");
    setUserEmail("");
    setUserPassword("SyntheticPass123!");
    setGrantProjectId("");
    setGrantEnvironmentId("");
    setGrantDomainName("");
    setGrantUserId("");
    setGrantRoleId("");
    setAccessPolicyProjectId("");
    setAccessPolicyName("");
    setAccessPolicyVisibility("PRIVATE");
    setAccessPolicyDomainName("");
    setAccessPolicyRuleJson("{\"mode\":\"domain_role\"}");
    setOperationMessage(null);
    setOperationError(null);
  };

  const handleSelectJob = (jobId: string) => {
    if (jobId === effectiveSelectedJobId) return;
    setSelectedJobId(jobId);
    setOperationMessage(null);
    setOperationError(null);
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

  const handleCreateRole = async () => {
    const name = roleName.trim();
    const capability_names = roleCapabilityNames
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);
    if (!name) {
      setOperationError("Role name is required.");
      return;
    }
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const role = await createRole(token, { capability_names, name });
      setRoleName("");
      setRoleCapabilityNames("");
      setGrantRoleId(role.id);
      setOperationMessage(`Created role ${role.name}.`);
      await refreshSetupData(selectedProfileProjectId || projectId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create role.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateUser = async () => {
    const email = userEmail.trim();
    if (!email || !userPassword) {
      setOperationError("User email and password are required.");
      return;
    }
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const created = await createUser(token, { email, is_active: true, password: userPassword });
      setUserEmail("");
      setGrantUserId(created.id);
      setOperationMessage(`Created user ${created.email}.`);
      await refreshSetupData(projectId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create user.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateGrant = async () => {
    const selectedGrantProjectId = grantProjectId || accessModel.data?.active_project_id || projectItems[0]?.id || "";
    const selectedGrantEnvironmentId = grantEnvironmentId || selectedGrantProjectEnvironments.data?.items[0]?.id || null;
    const selectedGrantRoleId = grantRoleId || accessModel.data?.roles[0]?.id || "";
    const userId = grantUserId || accessModel.data?.users.find((item) => !item.is_admin)?.id || "";
    if (!selectedGrantProjectId || !selectedGrantRoleId || !userId) {
      setOperationError("Grant project, role, and user ID are required.");
      return;
    }
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const grant = await createGrant(token, {
        domain_name: grantDomainName.trim() || null,
        environment_id: selectedGrantEnvironmentId,
        project_id: selectedGrantProjectId,
        role_id: selectedGrantRoleId,
        user_id: userId
      });
      setGrantUserId("");
      setOperationMessage(`Assigned ${grant.role_name ?? "role"} to ${grant.user_email ?? grant.user_id}.`);
      await Promise.all([
        refreshSetupData(selectedGrantProjectId),
        queryClient.invalidateQueries({ queryKey: ["platform", "active-context", "capabilities"] })
      ]);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not assign grant.");
    } finally {
      setIsMutating(false);
    }
  };

  const handleCreateAccessPolicy = async () => {
    const selectedPolicyProjectId = accessPolicyProjectId || accessModel.data?.active_project_id || projectItems[0]?.id || null;
    const name = accessPolicyName.trim();
    const domainName = accessPolicyDomainName.trim();
    if (!name) {
      setOperationError("Access policy name is required.");
      return;
    }
    setIsMutating(true);
    setOperationError(null);
    setOperationMessage(null);
    try {
      const policy = await createAccessPolicy(token, {
        domain_name: domainName || null,
        name,
        project_id: selectedPolicyProjectId,
        rule_json: accessPolicyRuleJson || "{}",
        visibility: accessPolicyVisibility
      });
      setAccessPolicyName("");
      setOperationMessage(`Created access policy ${policy.name}.`);
      await refreshSetupData(selectedPolicyProjectId);
    } catch (error) {
      setOperationError(error instanceof Error ? error.message : "Could not create access policy.");
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
    scopeAuthority.isLoading ||
    accessModel.isLoading ||
    (Boolean(projectId) && setupStatus.isLoading);

  if (isLoading) {
    return <StatePanel>Loading Settings...</StatePanel>;
  }

  if (
    currentUser.isError ||
    workspaces.isError ||
    projects.isError ||
    capabilities.isError ||
    jobs.isError ||
    auditLogs.isError ||
    scopeAuthority.isError ||
    accessModel.isError
  ) {
    return <StatePanel tone="error">Settings is unavailable.</StatePanel>;
  }

  const auditItems = auditLogs.data?.items ?? [];
  const featureFlagItems = featureFlags.data?.items ?? [];
  const eventItems = selectedJobEvents.data?.items ?? [];
  const capabilityItems = capabilities.data?.capabilities ?? [];
  const roleItems = capabilities.data?.roles ?? [];
  const setup = setupStatus.data;
  const authority = scopeAuthority.data;
  const access = accessModel.data;
  const setupVisibility = access?.setup_visibility;
  const canCreateDemoJob = Boolean(projectId && profileId && environmentId) && !isMutating;
  const profileAuthoringItems = selectedProjectProfiles.data?.items ?? [];
  const environmentAuthoringItems = selectedProjectEnvironments.data?.items ?? [];
  const roleAuthoringItems = access?.roles ?? [];
  const userAuthoringItems = access?.users ?? [];
  const grantAuthoringItems = access?.grants ?? [];
  const accessPolicyItems = access?.access_policies ?? [];
  const selectedGrantProjectId = grantProjectId || access?.active_project_id || projectItems[0]?.id || "";
  const grantEnvironmentItems = selectedGrantProjectEnvironments.data?.items ?? [];
  const selectedGrantEnvironmentId = grantEnvironmentId || grantEnvironmentItems[0]?.id || "";
  const selectedGrantRoleId = grantRoleId || roleAuthoringItems[0]?.id || "";
  const selectedGrantUserId = grantUserId || userAuthoringItems.find((item) => !item.is_admin)?.id || "";
  const selectedAccessPolicyProjectId = accessPolicyProjectId || access?.active_project_id || projectItems[0]?.id || "";

  return (
    <>
      <PageHeader
        description="Project, client/domain, environment, users, roles, grants, policies, jobs, and audit visibility for backend-owned setup contracts."
        label="Configuration"
        title="Settings"
      />

      <MetricGrid
        ariaLabel="Settings metrics"
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

      <OperationalPanel
        ariaLabel="Settings scope authority"
        emptyText="Settings scope authority is unavailable."
        hasItems={Boolean(authority)}
        status={authority?.status ?? "UNKNOWN"}
        title="Scope authority"
      >
        {authority ? (
          <div className="admin-scope-authority">
            <MetricGrid
              ariaLabel="Settings scope setup counts"
              items={[
                {
                  key: "workspaces",
                  label: "Workspaces",
                  status: booleanStatus(authority.setup_counts.workspaces),
                  value: authority.setup_counts.workspaces
                },
                {
                  key: "projects",
                  label: "Projects",
                  status: booleanStatus(authority.setup_counts.projects),
                  value: authority.setup_counts.projects
                },
                {
                  key: "profiles",
                  label: "Profiles",
                  status: booleanStatus(authority.setup_counts.profiles),
                  value: authority.setup_counts.profiles
                },
                {
                  key: "environments",
                  label: "Environments",
                  status: booleanStatus(authority.setup_counts.environments),
                  value: authority.setup_counts.environments
                }
              ]}
            />
            <div className="admin-scope-authority-grid">
              <div aria-label="Settings scope blockers" className="admin-scope-authority-list">
                <strong>Blocked reasons</strong>
                {authority.blocked_reasons.length ? (
                  authority.blocked_reasons.map((reason) => <span key={reason}>{reason}</span>)
                ) : (
                  <span>READY</span>
                )}
              </div>
              <div aria-label="Settings scope active context" className="admin-scope-authority-list">
                <strong>Active context</strong>
                <span>{contextValue(authority.active_context.project_id)}</span>
                <span>{contextValue(authority.active_context.environment_id)}</span>
                <span>{contextValue(authority.active_context.domain_name)}</span>
              </div>
              <div aria-label="Settings setup visibility" className="admin-scope-authority-list">
                <strong>Setup visibility</strong>
                <span>{authority.setup_visibility.level}</span>
                <span>Profiles: {authority.setup_visibility.can_manage_profiles ? "Manage" : "Read"}</span>
                <span>Grants: {authority.setup_visibility.can_manage_grants ? "Manage" : "Read"}</span>
                <span>Policies: {authority.setup_visibility.can_manage_access_policies ? "Manage" : "Read"}</span>
              </div>
              <div aria-label="Settings scope actions" className="admin-scope-authority-list">
                <strong>Available actions</strong>
                {authority.available_actions.map((action) => (
                  <span key={action.key}>
                    {action.label}
                    {action.disabled_reason ? ` / ${action.disabled_reason}` : ""}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </OperationalPanel>

      <ModuleWorkspaceLayout
        ariaLabel="Platform jobs"
        side={
          <ModuleWorkspaceSide ariaLabel="Admin setup and capability details" title="Setup and access">
            <OperationalPanel
              ariaLabel="Setup authoring"
              emptyText="No setup entities available."
              hasItems={Boolean(authority) || workspaceItems.length > 0 || projectItems.length > 0}
              status={projectItems.length ? "ACTIVE" : "EMPTY"}
              title="Setup authoring"
            >
              <div className="admin-console-actions">
                <Button disabled={isMutating} onClick={resetSetupDrafts} type="button">
                  Reset setup drafts
                </Button>
                <a className="button button-secondary" href="/home">
                  Return to Cockpit
                </a>
              </div>
              <div aria-label="Setup action recovery" className="admin-setup-recovery">
                <div className="admin-setup-list">
                  {authority?.blocked_reasons.length ? (
                    authority.blocked_reasons.map((reason) => <span key={reason}>{reason}</span>)
                  ) : (
                    <span>READY</span>
                  )}
                </div>
                <div className="admin-setup-list">
                  {authority?.available_actions.map((action) => (
                    <span key={action.key}>
                      {action.label}
                      {action.disabled_reason ? ` / ${action.disabled_reason}` : ""}
                    </span>
                  ))}
                </div>
              </div>
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
                  <Button disabled={isMutating || !setupVisibility?.can_manage_workspaces} type="submit" variant="primary">
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
                      {!workspaceItems.length ? <option value="">Workspace required</option> : null}
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
                  <Button disabled={isMutating || !setupVisibility?.can_manage_projects || !workspaceItems.length} type="submit" variant="primary">
                    Create project
                  </Button>
                  {!workspaceItems.length ? <span className="admin-setup-hint">Workspace required</span> : null}
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
                      {!projectItems.length ? <option value="">Project required</option> : null}
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
                  <Button disabled={isMutating || !setupVisibility?.can_manage_profiles || !projectItems.length} type="submit" variant="primary">
                    Create profile
                  </Button>
                  {!projectItems.length ? <span className="admin-setup-hint">Project required</span> : null}
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
                      {!projectItems.length ? <option value="">Project required</option> : null}
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
                  <Button disabled={isMutating || !setupVisibility?.can_manage_environments || !projectItems.length} type="submit" variant="primary">
                    Create environment
                  </Button>
                  {!projectItems.length ? <span className="admin-setup-hint">Project required</span> : null}
                  <div className="admin-setup-list">
                    {environmentAuthoringItems.slice(-3).map((environment) => (
                      <span key={environment.id}>{environment.name}</span>
                    ))}
                  </div>
                </form>

                <form
                  aria-label="Role authoring"
                  className="admin-setup-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreateRole();
                  }}
                >
                  <label>
                    Role name
                    <input onChange={(event) => setRoleName(event.target.value)} placeholder="Rates operator" value={roleName} />
                  </label>
                  <label>
                    Capabilities
                    <input
                      onChange={(event) => setRoleCapabilityNames(event.target.value)}
                      placeholder="rates.batch.view, rates.batch.export"
                      value={roleCapabilityNames}
                    />
                  </label>
                  <Button disabled={isMutating || !setupVisibility?.can_manage_roles} type="submit" variant="primary">
                    Create role
                  </Button>
                  <div className="admin-setup-list">
                    {roleAuthoringItems.slice(-3).map((role) => (
                      <span key={role.id}>{role.name}</span>
                    ))}
                  </div>
                </form>

                <form
                  aria-label="User authoring"
                  className="admin-setup-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreateUser();
                  }}
                >
                  <label>
                    User email
                    <input onChange={(event) => setUserEmail(event.target.value)} placeholder="operator@example.test" value={userEmail} />
                  </label>
                  <label>
                    Temporary password
                    <input onChange={(event) => setUserPassword(event.target.value)} type="password" value={userPassword} />
                  </label>
                  <Button disabled={isMutating || !setupVisibility?.can_manage_users} type="submit" variant="primary">
                    Create user
                  </Button>
                  <div className="admin-setup-list">
                    {userAuthoringItems.slice(-3).map((item) => (
                      <span key={item.id}>{item.email}</span>
                    ))}
                  </div>
                </form>

                <form
                  aria-label="Grant authoring"
                  className="admin-setup-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreateGrant();
                  }}
                >
                  <label>
                    Grant project
                    <select onChange={(event) => setGrantProjectId(event.target.value)} value={selectedGrantProjectId}>
                      {!projectItems.length ? <option value="">Project required</option> : null}
                      {projectItems.map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Grant role
                    <select onChange={(event) => setGrantRoleId(event.target.value)} value={selectedGrantRoleId}>
                      {!roleAuthoringItems.length ? <option value="">Role required</option> : null}
                      {roleAuthoringItems.map((role) => (
                        <option key={role.id} value={role.id}>
                          {role.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Grant environment
                    <select onChange={(event) => setGrantEnvironmentId(event.target.value)} value={selectedGrantEnvironmentId}>
                      {!grantEnvironmentItems.length ? <option value="">Environment required</option> : null}
                      {grantEnvironmentItems.map((environment) => (
                        <option key={environment.id} value={environment.id}>
                          {environment.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Grant domain
                    <input onChange={(event) => setGrantDomainName(event.target.value)} placeholder="OTM1" value={grantDomainName} />
                  </label>
                  <label>
                    Grant user
                    <select onChange={(event) => setGrantUserId(event.target.value)} value={selectedGrantUserId}>
                      {!userAuthoringItems.length ? <option value="">User required</option> : null}
                      {userAuthoringItems.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.email}
                        </option>
                      ))}
                    </select>
                  </label>
                  <Button
                    disabled={isMutating || !setupVisibility?.can_manage_grants || !roleAuthoringItems.length || !userAuthoringItems.length}
                    type="submit"
                    variant="primary"
                  >
                    Assign grant
                  </Button>
                  {!projectItems.length ? <span className="admin-setup-hint">Project required</span> : null}
                  {!roleAuthoringItems.length ? <span className="admin-setup-hint">Role required</span> : null}
                  {!userAuthoringItems.length ? <span className="admin-setup-hint">User required</span> : null}
                  <div className="admin-setup-list">
                    {grantAuthoringItems.slice(-3).map((grant) => (
                      <span key={grant.id}>
                        {grant.user_email ?? grant.user_id} / {grant.role_name ?? grant.role_id} / {grant.binding_scope_label}
                      </span>
                    ))}
                  </div>
                </form>

                <div aria-label="Grant binding review" className="admin-policy-binding-review">
                  {grantAuthoringItems.length ? (
                    grantAuthoringItems.map((grant) => (
                      <article className="admin-policy-binding-card" key={grant.id}>
                        <div>
                          <strong>{grant.user_email ?? grant.user_id}</strong>
                          <span>
                            {grant.role_name ?? grant.role_id} / {grant.binding_scope_label}
                          </span>
                        </div>
                        <StatusChip status={grant.active_context_match ? "READY" : grant.active_context_disabled_reason ?? "BLOCKED"} />
                        <div className="admin-policy-binding-rules">
                          {grant.binding_requirements.map((requirement) => (
                            <span key={requirement}>{requirement}</span>
                          ))}
                        </div>
                      </article>
                    ))
                  ) : (
                    <span className="empty-text">No grants to review.</span>
                  )}
                </div>

                <form
                  aria-label="Access policy authoring"
                  className="admin-setup-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void handleCreateAccessPolicy();
                  }}
                >
                  <label>
                    Policy project
                    <select onChange={(event) => setAccessPolicyProjectId(event.target.value)} value={selectedAccessPolicyProjectId}>
                      {!projectItems.length ? <option value="">Project required</option> : null}
                      {projectItems.map((project) => (
                        <option key={project.id} value={project.id}>
                          {project.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Policy name
                    <input
                      onChange={(event) => setAccessPolicyName(event.target.value)}
                      placeholder="Domain role policy"
                      value={accessPolicyName}
                    />
                  </label>
                  <label>
                    Visibility
                    <select onChange={(event) => setAccessPolicyVisibility(event.target.value)} value={accessPolicyVisibility}>
                      <option value="PRIVATE">PRIVATE</option>
                      <option value="PROJECT">PROJECT</option>
                      <option value="PUBLIC">PUBLIC</option>
                    </select>
                  </label>
                  <label>
                    Domain
                    <input
                      onChange={(event) => setAccessPolicyDomainName(event.target.value)}
                      placeholder="OTM1"
                      value={accessPolicyDomainName}
                    />
                  </label>
                  <label>
                    Rule JSON
                    <input onChange={(event) => setAccessPolicyRuleJson(event.target.value)} value={accessPolicyRuleJson} />
                  </label>
                  <Button disabled={isMutating || !setupVisibility?.can_manage_access_policies} type="submit" variant="primary">
                    Create access policy
                  </Button>
                  {!projectItems.length ? <span className="admin-setup-hint">Project required</span> : null}
                  <div className="admin-setup-list">
                    {accessPolicyItems.slice(-3).map((policy) => (
                      <span key={policy.id}>
                        {policy.name} / {policy.binding_scope_label}
                      </span>
                    ))}
                  </div>
                </form>

                <div aria-label="Access policy binding review" className="admin-policy-binding-review">
                  {accessPolicyItems.length ? (
                    accessPolicyItems.map((policy) => (
                      <article className="admin-policy-binding-card" key={policy.id}>
                        <div>
                          <strong>{policy.name}</strong>
                          <span>{policy.binding_scope_label}</span>
                        </div>
                        <StatusChip status={policy.active_context_match ? "READY" : policy.active_context_disabled_reason ?? "BLOCKED"} />
                        <div className="admin-policy-binding-rules">
                          {policy.binding_requirements.map((requirement) => (
                            <span key={requirement}>{requirement}</span>
                          ))}
                        </div>
                      </article>
                    ))
                  ) : (
                    <span className="empty-text">No access policies to review.</span>
                  )}
                </div>
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
                <Button aria-label={`View events ${job.id}`} disabled={isMutating} onClick={() => handleSelectJob(job.id)}>
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
          maxVisibleItems={10}
        />
      </ModuleWorkspaceLayout>
    </>
  );
}
