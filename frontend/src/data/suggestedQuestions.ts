
import type { DemoUser } from './demoUsers'

export interface SuggestedQuestion {
  id: string
  question: string
  description: string
  relevantRoles: readonly string[]
  public?: boolean
}

export const PLACEHOLDER_QUESTIONS = [
  '¿Dónde es el punto de encuentro durante una evacuación?',
  '¿Hasta cuánto puede autorizar un vendedor en descuentos?',
  '¿Qué margen tiene la línea refrigerada?',
  '¿Qué valores representan a Andino?',
]

const QUESTIONS: SuggestedQuestion[] = [
  {
    id: 'company-values',
    question: '¿Cuáles son los valores de Andino y qué significan?',
    description: 'Conocé los principios y valores de la empresa',
    relevantRoles: [],
    public: true,
  },
  {
    id: 'emergency',
    question: '¿Dónde es el punto de encuentro si suena la alarma de evacuación?',
    description: 'Seguridad · Protocolo de evacuación',
    relevantRoles: ['Employee'],
  },
  {
    id: 'sales-discounts',
    question: '¿Hasta cuánto puedo dar de descuento y quién tiene que autorizar el máximo?',
    description: 'Ventas · Límites y niveles de autorización',
    relevantRoles: ['Sales'],
  },
  {
    id: 'finance-margins',
    question: '¿Qué margen tiene la línea refrigerada?',
    description: 'Finanzas · Acceso a información de márgenes',
    relevantRoles: ['Finance'],
  },
  {
    id: 'management-decisions',
    question: '¿Qué se resolvió sobre las horas extra y las contrataciones?',
    description: 'Dirección · Decisiones internas de la empresa',
    relevantRoles: ['Finance', 'HR'],
  },
]

export function getSuggestedQuestions(
  users: DemoUser[],
): SuggestedQuestion[] {
  if (users.length === 0) return []

  const hasRole = (role: string) =>
    users.some((user) => user.roles.includes(role))

  const hasVisitor = users.some((user) => user.roles.length === 0)

  return QUESTIONS.filter((question) => {
    // Las preguntas públicas aparecen cuando Visitor está seleccionado.
    if (question.public) return hasVisitor

    return question.relevantRoles.some(hasRole)
  }).map((question) => {
    if (question.id === 'finance-margins') {
      const hasFinance = hasRole('Finance')
      const hasSales = hasRole('Sales')

      if (hasFinance && hasSales) {
        return {
          ...question,
          description: 'Comparación de permisos · Finanzas vs. Ventas',
        }
      }
    }

    return question
  })
}
