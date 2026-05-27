import { type FormEvent, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ApiError } from "../../platform/api";
import { updateActiveContext, useEnvironments, useProfiles, useProjects } from "../../platform/hooks";
import type { ActiveContextResponse } from "../../platform/types";
import { Button, FeedbackMessage } from "../../ui/components";

export function ContextSwitcher({ activeContext, token }: { activeContext?: Partial<ActiveContextResponse>; token: string }) {
  const queryClient = useQueryClient();
  const projects = useProjects(token);
  const [projectId, setProjectId] = useState<string>("");
  const [profileId, setProfileId] = useState<string>("");
  const [environmentId, setEnvironmentId] = useState<string>("");
  const [domainName, setDomainName] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);
  const profiles = useProfiles(token, projectId || null);
  const environments = useEnvironments(token, projectId || null);

  useEffect(() => {
    setProjectId(activeContext?.project_id ?? "");
    setProfileId(activeContext?.profile_id ?? "");
    setEnvironmentId(activeContext?.environment_id ?? "");
    setDomainName(activeContext?.domain_name ?? "");
    clearDraftFeedback();
  }, [
    activeContext?.domain_name,
    activeContext?.environment_id,
    activeContext?.profile_id,
    activeContext?.project_id
  ]);

  function clearDraftFeedback() {
    setMessage(null);
    setError(null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setSubmitting(true);
    try {
      await updateActiveContext(token, {
        project_id: projectId || null,
        profile_id: profileId || null,
        environment_id: environmentId || null,
        domain_name: domainName || null,
        can_view_all_domains: false
      });
      await queryClient.invalidateQueries({ queryKey: ["platform"] });
      setMessage("Context updated.");
    } catch (caught) {
      if (caught instanceof ApiError) {
        setError(caught.message);
      } else {
        setError("Unable to update context.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="context-switcher" onSubmit={handleSubmit}>
      <label>
        <span>Project</span>
        <select
          disabled={projects.isLoading}
          onChange={(event) => {
            setProjectId(event.target.value);
            setProfileId("");
            setEnvironmentId("");
            clearDraftFeedback();
          }}
          value={projectId}
        >
          <option value="">Select project</option>
          {(projects.data?.items ?? []).map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Profile</span>
        <select
          disabled={!projectId || profiles.isLoading}
          onChange={(event) => {
            setProfileId(event.target.value);
            clearDraftFeedback();
          }}
          value={profileId}
        >
          <option value="">Select profile</option>
          {(profiles.data?.items ?? []).map((profile) => (
            <option key={profile.id} value={profile.id}>
              {profile.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Environment</span>
        <select
          disabled={!projectId || environments.isLoading}
          onChange={(event) => {
            setEnvironmentId(event.target.value);
            clearDraftFeedback();
          }}
          value={environmentId}
        >
          <option value="">Select environment</option>
          {(environments.data?.items ?? []).map((environment) => (
            <option key={environment.id} value={environment.id}>
              {environment.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Domain</span>
        <input
          onChange={(event) => {
            setDomainName(event.target.value);
            clearDraftFeedback();
          }}
          placeholder="PUBLIC"
          value={domainName}
        />
      </label>
      <Button disabled={isSubmitting || !projectId} type="submit" variant="primary">
        {isSubmitting ? "Applying..." : "Apply context"}
      </Button>
      {message ? <FeedbackMessage tone="success">{message}</FeedbackMessage> : null}
      {error ? <FeedbackMessage tone="error">{error}</FeedbackMessage> : null}
    </form>
  );
}
