/**
 * CLIMORA Frontend API Service
 * Encapsulates all communication with the canonical Flask backend.
 * Zero client-side recalculation.
 * Enforces server-side Cedar governance authorization via X-Climora-Actor.
 */

import {
  AllocationResponse,
  BaselineResponse,
  GovernanceActor,
  GovernanceAuditRecord,
  GovernanceCheckResult,
  MRVOverviewResponse,
  ProjectSummary,
  RiskSurfaceResponse,
  ScenarioOptimizeResponse,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export const CANONICAL_PROJECT_ID = 'PROJ-PUNE-2025-BA225D6A';

let currentActorId = 'pmc_commissioner';

type ActorChangeListener = (actorId: string) => void;
const actorListeners: Set<ActorChangeListener> = new Set();

export function onActorChange(listener: ActorChangeListener): () => void {
  actorListeners.add(listener);
  return () => {
    actorListeners.delete(listener);
  };
}

export function setCurrentActor(actorId: string): void {
  currentActorId = actorId;
  actorListeners.forEach((fn) => fn(actorId));
}

export function getCurrentActor(): string {
  return currentActorId;
}

function getAuthHeaders(additionalHeaders: Record<string, string> = {}): Record<string, string> {
  return {
    'X-Climora-Actor': currentActorId,
    ...additionalHeaders,
  };
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: Record<string, any> = {}
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errBody: any = {};
    try {
      errBody = await res.json();
    } catch {
      // Body not JSON
    }
    const code = errBody?.error?.code || `HTTP_${res.status}`;
    const message = errBody?.error?.message || errBody?.reason || res.statusText || 'An error occurred while fetching data.';
    const details = errBody?.error?.details || errBody || {};
    throw new ApiError(res.status, code, message, details);
  }
  return res.json();
}

export const climoraApi = {
  /**
   * GET /projects/governance/actors
   * Returns registered demo personas for Cedar policy evaluation.
   */
  async getGovernanceActors(): Promise<GovernanceActor[]> {
    const res = await fetch(`${API_BASE}/projects/governance/actors`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<{ status: string; count: number; actors: GovernanceActor[] }>(res);
    return json.actors;
  },

  /**
   * GET /projects/{project_id}/governance-audit
   * Returns recent Cedar authorization decisions for the project.
   */
  async getGovernanceAudit(projectId = CANONICAL_PROJECT_ID): Promise<GovernanceAuditRecord[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/governance-audit`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<{ status: string; audit_trail: GovernanceAuditRecord[] }>(res);
    return json.audit_trail;
  },

  /**
   * POST /projects/{project_id}/governance-check
   * Dry-run Cedar policy check without state mutation.
   */
  async checkGovernance(
    projectId: string,
    action: string,
    actor?: string
  ): Promise<GovernanceCheckResult> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/governance-check`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        action,
        actor: actor || currentActorId,
      }),
    });
    const json = await handleResponse<{ status: string; check: GovernanceCheckResult }>(res);
    return json.check;
  },

  /**
   * GET /projects
   * Returns list of canonical projects.
   */
  async listProjects(): Promise<ProjectSummary[]> {
    const res = await fetch(`${API_BASE}/projects`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<{ status: string; projects: ProjectSummary[] }>(res);
    return json.projects;
  },

  /**
   * GET /projects/{project_id}
   */
  async getProjectDetail(projectId = CANONICAL_PROJECT_ID): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${projectId}`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<{ status: string; project: any }>(res);
    return json.project;
  },

  /**
   * GET /projects/{project_id}/allocation
   * Returns immutable canonical cell allocation records.
   */
  async getAllocation(
    projectId = CANONICAL_PROJECT_ID,
    h3CellId?: string,
    page = 1,
    pageSize = 28
  ): Promise<AllocationResponse['data']> {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (h3CellId) {
      params.append('h3_cell_id', h3CellId);
    }
    const res = await fetch(`${API_BASE}/projects/${projectId}/allocation?${params.toString()}`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<AllocationResponse>(res);
    return json.data;
  },

  /**
   * PUT /projects/{project_id}/allocation
   * Attempt direct mutation of canonical allocation (triggers Cedar negative policy).
   */
  async attemptAllocationMutation(projectId = CANONICAL_PROJECT_ID, payload = { quantity: 9999 }): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/allocation`, {
      method: 'PUT',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  /**
   * GET /projects/{project_id}/baseline
   * Exposes observed and derived multi-year baseline evidence.
   */
  async getBaseline(
    projectId = CANONICAL_PROJECT_ID,
    h3CellId?: string,
    page = 1,
    pageSize = 28
  ): Promise<BaselineResponse['data']> {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    if (h3CellId) {
      params.append('h3_cell_id', h3CellId);
    }
    const res = await fetch(`${API_BASE}/projects/${projectId}/baseline?${params.toString()}`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<BaselineResponse>(res);
    return json.data;
  },

  /**
   * GET /projects/{project_id}/mrv
   * Returns MRV tracking and readiness status.
   */
  async getMRV(projectId = CANONICAL_PROJECT_ID): Promise<MRVOverviewResponse['data']> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/mrv`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<MRVOverviewResponse>(res);
    return json.data;
  },

  /**
   * POST /projects/{project_id}/transition
   * Transitions project lifecycle state guarded by Cedar authorization.
   */
  async transitionState(
    projectId: string,
    targetState: string,
    sanctionId?: string,
    approvedBudgetInr?: number,
    notes?: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/transition`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        target_state: targetState,
        sanction_id: sanctionId,
        approved_budget_inr: approvedBudgetInr,
        notes,
      }),
    });
    return handleResponse(res);
  },

  /**
   * POST /projects/{project_id}/revisions
   * Proposes an auditable allocation revision without mutating canonical truth.
   */
  async proposeRevision(
    projectId: string,
    h3CellId: string,
    interventionCode: string,
    proposedQuantity: number,
    reason: string,
    author: string
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/revisions`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        h3_cell_id: h3CellId,
        intervention_code: interventionCode,
        proposed_quantity: proposedQuantity,
        reason,
        author,
      }),
    });
    return handleResponse(res);
  },

  /**
   * POST /projects/{project_id}/implementation-events
   * Logs contractor deployment progress.
   */
  async recordImplementationEvent(projectId: string, payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/implementation-events`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  /**
   * GET /projects/{project_id}/risk-surface
   * Returns citywide canonical H3 risk surface (3,181 cells).
   */
  async getRiskSurface(projectId = CANONICAL_PROJECT_ID): Promise<RiskSurfaceResponse['data']> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/risk-surface`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<RiskSurfaceResponse>(res);
    return json.data;
  },

  /**
   * GET /projects/{project_id}/boundary
   * Returns canonical Pune AOI GeoJSON boundary.
   */
  async getPuneBoundary(projectId = CANONICAL_PROJECT_ID): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/boundary`, {
      headers: getAuthHeaders(),
    });
    const json = await handleResponse<{ status: string; boundary: any }>(res);
    return json.boundary;
  },

  /**
   * POST /projects/{project_id}/scenarios/optimize
   * Simulates an in-memory budget optimization scenario.
   */
  async optimizeScenario(
    projectId = CANONICAL_PROJECT_ID,
    budgetInr: number
  ): Promise<ScenarioOptimizeResponse['data']> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/scenarios/optimize`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ budget_inr: budgetInr }),
    });
    const json = await handleResponse<ScenarioOptimizeResponse>(res);
    return json.data;
  },
};
