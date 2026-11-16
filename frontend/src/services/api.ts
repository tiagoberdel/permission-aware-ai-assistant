
export type DemoUserId =
  | 'diego'
  | 'sofia'
  | 'valentina'
  | 'martin'
  | 'laura'
  | 'ramon'
  | 'visitor'

export interface DemoSession {
  access_token: string
  token_type: string
  conversation_id: string
}

export interface AgentAnswer {
  answer: string
}

const API_BASE_URL = '/api'

async function getErrorMessage(response: Response): Promise<string> {
  const data: unknown = await response.json().catch(() => null)

  if (
    typeof data === 'object' &&
    data !== null &&
    'detail' in data &&
    typeof data.detail === 'string'
  ) {
    return data.detail
  }

  return `API request failed (${response.status})`
}

export async function createDemoSession(
  demoUser: DemoUserId,
): Promise<DemoSession> {
  const response = await fetch(`${API_BASE_URL}/demo/sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ demo_user: demoUser }),
  })

  if (!response.ok) {
    throw new Error(await getErrorMessage(response))
  }

  return response.json() as Promise<DemoSession>
}

export async function askAgent(
  accessToken: string,
  query: string,
): Promise<AgentAnswer> {
  const response = await fetch(`${API_BASE_URL}/agent/ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ query }),
  })

  if (!response.ok) {
    throw new Error(await getErrorMessage(response))
  }

  return response.json() as Promise<AgentAnswer>
}
