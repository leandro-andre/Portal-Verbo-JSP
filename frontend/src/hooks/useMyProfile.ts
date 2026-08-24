import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  deleteMyProfilePhoto,
  getMyProfile,
  updateMyProfile,
  uploadMyProfilePhoto,
} from '../api/profile'
import type { MyProfileUpdateInput } from '../types/person'
import { myDashboardQueryKey } from './useDashboard'
import { currentUserQueryKey } from './useAuth'

export const myProfileQueryKey = ['me', 'profile'] as const

export function useMyProfile() {
  return useQuery({
    queryKey: myProfileQueryKey,
    queryFn: getMyProfile,
  })
}

export function useMyProfileMutations() {
  const queryClient = useQueryClient()
  const onSuccess = async () => {
    await queryClient.invalidateQueries({ queryKey: myProfileQueryKey })
    await queryClient.invalidateQueries({ queryKey: myDashboardQueryKey })
    await queryClient.invalidateQueries({ queryKey: currentUserQueryKey })
  }

  return {
    update: useMutation({ mutationFn: (payload: MyProfileUpdateInput) => updateMyProfile(payload), onSuccess }),
    uploadPhoto: useMutation({ mutationFn: (photo: File) => uploadMyProfilePhoto(photo), onSuccess }),
    deletePhoto: useMutation({ mutationFn: deleteMyProfilePhoto, onSuccess }),
  }
}
