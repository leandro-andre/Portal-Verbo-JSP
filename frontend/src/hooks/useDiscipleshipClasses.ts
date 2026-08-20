import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  cancelDiscipleshipClass,
  cancelDiscipleshipLesson,
  completeDiscipleshipClass,
  completeDiscipleshipEnrollment,
  createDiscipleshipEnrollment,
  createDiscipleshipClass,
  createDiscipleshipLesson,
  getDiscipleshipClass,
  getDiscipleshipClasses,
  getDiscipleshipCompletion,
  getDiscipleshipAttendance,
  getDiscipleshipEnrollment,
  getDiscipleshipEnrollments,
  getDiscipleshipLesson,
  getDiscipleshipLessons,
  saveDiscipleshipAttendance,
  startDiscipleshipClass,
  updateDiscipleshipClass,
  updateDiscipleshipLesson,
  withdrawDiscipleshipEnrollment,
} from '../api/discipleship'
import type {
  CreateDiscipleshipClassInput,
  CreateDiscipleshipEnrollmentInput,
  CreateDiscipleshipLessonInput,
  SaveDiscipleshipAttendanceInput,
  UpdateDiscipleshipClassInput,
  UpdateDiscipleshipLessonInput,
} from '../types/discipleship'

export const discipleshipClassesQueryKey = ['discipleship', 'classes'] as const

export function discipleshipClassQueryKey(id: number) {
  return ['discipleship', 'classes', id] as const
}

export function discipleshipEnrollmentsQueryKey(classId: number) {
  return ['discipleship', 'classes', classId, 'enrollments'] as const
}

export function discipleshipEnrollmentQueryKey(classId: number, enrollmentId: number) {
  return ['discipleship', 'classes', classId, 'enrollments', enrollmentId] as const
}

export function discipleshipLessonsQueryKey(classId: number) {
  return ['discipleship', 'classes', classId, 'lessons'] as const
}

export function discipleshipLessonQueryKey(classId: number, lessonId: number) {
  return ['discipleship', 'classes', classId, 'lessons', lessonId] as const
}

export function discipleshipAttendanceQueryKey(classId: number, lessonId: number) {
  return ['discipleship', 'classes', classId, 'lessons', lessonId, 'attendance'] as const
}

export function discipleshipCompletionQueryKey(classId: number, enrollmentId: number) {
  return ['discipleship', 'classes', classId, 'enrollments', enrollmentId, 'completion'] as const
}

export function useDiscipleshipClasses() {
  return useQuery({
    queryKey: discipleshipClassesQueryKey,
    queryFn: getDiscipleshipClasses,
  })
}

export function useDiscipleshipClass(id: number) {
  return useQuery({
    queryKey: discipleshipClassQueryKey(id),
    queryFn: () => getDiscipleshipClass(id),
    enabled: Number.isFinite(id),
  })
}

export function useCreateDiscipleshipClass() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateDiscipleshipClassInput) => createDiscipleshipClass(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: discipleshipClassesQueryKey })
    },
  })
}

export function useUpdateDiscipleshipClass(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: UpdateDiscipleshipClassInput) => updateDiscipleshipClass(id, payload),
    onSuccess: async (discipleshipClass) => {
      queryClient.setQueryData(discipleshipClassQueryKey(id), discipleshipClass)
      await queryClient.invalidateQueries({ queryKey: discipleshipClassesQueryKey })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(id) })
    },
  })
}

export function useDiscipleshipClassLifecycle(id: number) {
  const queryClient = useQueryClient()

  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: discipleshipClassesQueryKey })
    await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(id) })
  }

  return {
    start: useMutation({ mutationFn: () => startDiscipleshipClass(id), onSuccess }),
    complete: useMutation({ mutationFn: () => completeDiscipleshipClass(id), onSuccess }),
    cancel: useMutation({ mutationFn: () => cancelDiscipleshipClass(id), onSuccess }),
  }
}

export function useDiscipleshipEnrollments(classId: number) {
  return useQuery({
    queryKey: discipleshipEnrollmentsQueryKey(classId),
    queryFn: () => getDiscipleshipEnrollments(classId),
    enabled: Number.isFinite(classId),
  })
}

export function useDiscipleshipEnrollment(classId: number, enrollmentId: number) {
  return useQuery({
    queryKey: discipleshipEnrollmentQueryKey(classId, enrollmentId),
    queryFn: () => getDiscipleshipEnrollment(classId, enrollmentId),
    enabled: Number.isFinite(classId) && Number.isFinite(enrollmentId),
  })
}

export function useCreateDiscipleshipEnrollment(classId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateDiscipleshipEnrollmentInput) => createDiscipleshipEnrollment(classId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: discipleshipEnrollmentsQueryKey(classId) })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(classId) })
    },
  })
}

export function useWithdrawDiscipleshipEnrollment(classId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (enrollmentId: number) => withdrawDiscipleshipEnrollment(classId, enrollmentId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: discipleshipEnrollmentsQueryKey(classId) })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(classId) })
    },
  })
}

export function useDiscipleshipLessons(classId: number) {
  return useQuery({
    queryKey: discipleshipLessonsQueryKey(classId),
    queryFn: () => getDiscipleshipLessons(classId),
    enabled: Number.isFinite(classId),
  })
}

export function useDiscipleshipLesson(classId: number, lessonId: number) {
  return useQuery({
    queryKey: discipleshipLessonQueryKey(classId, lessonId),
    queryFn: () => getDiscipleshipLesson(classId, lessonId),
    enabled: Number.isFinite(classId) && Number.isFinite(lessonId),
  })
}

export function useCreateDiscipleshipLesson(classId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CreateDiscipleshipLessonInput) => createDiscipleshipLesson(classId, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: discipleshipLessonsQueryKey(classId) })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(classId) })
    },
  })
}

export function useUpdateDiscipleshipLesson(classId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: UpdateDiscipleshipLessonInput }) =>
      updateDiscipleshipLesson(classId, id, payload),
    onSuccess: async (lesson) => {
      queryClient.setQueryData(discipleshipLessonQueryKey(classId, lesson.id), lesson)
      await queryClient.invalidateQueries({ queryKey: discipleshipLessonsQueryKey(classId) })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(classId) })
    },
  })
}

export function useCancelDiscipleshipLesson(classId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (lessonId: number) => cancelDiscipleshipLesson(classId, lessonId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: discipleshipLessonsQueryKey(classId) })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(classId) })
    },
  })
}

export function useDiscipleshipAttendance(classId: number, lessonId: number) {
  return useQuery({
    queryKey: discipleshipAttendanceQueryKey(classId, lessonId),
    queryFn: () => getDiscipleshipAttendance(classId, lessonId),
    enabled: Number.isFinite(classId) && Number.isFinite(lessonId),
  })
}

export function useSaveDiscipleshipAttendance(classId: number, lessonId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: SaveDiscipleshipAttendanceInput) =>
      saveDiscipleshipAttendance(classId, lessonId, payload),
    onSuccess: async (attendance) => {
      queryClient.setQueryData(discipleshipAttendanceQueryKey(classId, lessonId), attendance)
      await queryClient.invalidateQueries({ queryKey: discipleshipLessonsQueryKey(classId) })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(classId) })
    },
  })
}

export function useDiscipleshipCompletion(classId: number, enrollmentId: number) {
  return useQuery({
    queryKey: discipleshipCompletionQueryKey(classId, enrollmentId),
    queryFn: () => getDiscipleshipCompletion(classId, enrollmentId),
    enabled: Number.isFinite(classId) && Number.isFinite(enrollmentId),
  })
}

export function useCompleteDiscipleshipEnrollment(classId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (enrollmentId: number) => completeDiscipleshipEnrollment(classId, enrollmentId),
    onSuccess: async (completion) => {
      queryClient.setQueryData(
        discipleshipCompletionQueryKey(classId, completion.enrollment_id),
        completion,
      )
      await queryClient.invalidateQueries({ queryKey: discipleshipEnrollmentsQueryKey(classId) })
      await queryClient.invalidateQueries({ queryKey: discipleshipClassQueryKey(classId) })
    },
  })
}
