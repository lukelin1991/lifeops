import { api } from './client'
import { crudApi } from './crud'
import type {
  Certification,
  Contact,
  Interview,
  JobApplication,
  Pipeline,
} from './types'

export const careerApi = {
  applications: crudApi<JobApplication>('/career/applications'),
  interviews: crudApi<Interview>('/career/interviews'),
  contacts: crudApi<Contact>('/career/contacts'),
  certifications: crudApi<Certification>('/career/certifications'),

  pipeline: () => api.get<Pipeline>('/career/pipeline'),
}
