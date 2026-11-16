
import type { DemoUserId } from '../services/api'

export interface DemoUser {
  id: DemoUserId
  name: string
  jobTitle: string
  roles: string[]
}

export const DEMO_USERS: DemoUser[] = [
  {
    id: 'diego',
    name: 'Diego Martínez',
    jobTitle: 'Sales Manager',
    roles: ['Employee', 'Sales'],
  },
  {
    id: 'sofia',
    name: 'Sofía Gómez',
    jobTitle: 'Sales Representative',
    roles: ['Employee', 'Sales'],
  },
  {
    id: 'valentina',
    name: 'Valentina Silva',
    jobTitle: 'Finance Manager',
    roles: ['Employee', 'Finance'],
  },
  {
    id: 'martin',
    name: 'Martín Pérez',
    jobTitle: 'Finance Analyst',
    roles: ['Employee', 'Finance'],
  },
  {
    id: 'laura',
    name: 'Laura Fernández',
    jobTitle: 'HR Manager',
    roles: ['Employee', 'HR'],
  },
  {
    id: 'ramon',
    name: 'Ramón Rodríguez',
    jobTitle: 'Chief Executive Officer',
    roles: ['Employee', 'Sales', 'Finance', 'HR'],
  },
  {
    id: 'visitor',
    name: 'Visitor',
    jobTitle: 'External Visitor',
    roles: [],
  },
]
