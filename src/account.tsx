import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import {
  GoogleAuthProvider,
  deleteUser,
  onAuthStateChanged,
  reauthenticateWithPopup,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from 'firebase/auth'
import { collection, deleteDoc, doc, getDocs, writeBatch } from 'firebase/firestore'
import { auth, db, firebaseConfigured } from './firebase'

interface AccountContextValue {
  user: User | null
  ready: boolean
  configured: boolean
  loginOpen: boolean
  openLogin: () => void
  closeLogin: () => void
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
  deleteAccount: () => Promise<void>
}

const AccountContext = createContext<AccountContextValue | null>(null)

export function AccountProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [ready, setReady] = useState(!auth)
  const [loginOpen, setLoginOpen] = useState(false)

  useEffect(() => {
    if (!auth) return
    return onAuthStateChanged(auth, next => {
      setUser(next)
      setReady(true)
      if (next) setLoginOpen(false)
    }, () => setReady(true))
  }, [])

  const openLogin = () => setLoginOpen(true)
  const closeLogin = () => setLoginOpen(false)

  const signInWithGoogle = async () => {
    if (!auth) throw new Error('Firebase 설정이 아직 완료되지 않았습니다.')
    await signInWithPopup(auth, new GoogleAuthProvider())
  }

  const signOut = async () => {
    if (!auth) return
    await firebaseSignOut(auth)
  }

  const deleteAccount = async () => {
    if (!auth || !db || !user) throw new Error('로그인이 필요합니다.')
    await reauthenticateWithPopup(user, new GoogleAuthProvider())
    for (const name of ['favorites', 'keywords', 'notifications']) {
      const snapshot = await getDocs(collection(db, 'users', user.uid, name))
      for (let start = 0; start < snapshot.docs.length; start += 450) {
        const batch = writeBatch(db)
        for (const record of snapshot.docs.slice(start, start + 450)) batch.delete(record.ref)
        await batch.commit()
      }
    }
    await deleteDoc(doc(db, 'users', user.uid))
    await deleteUser(user)
  }

  const value: AccountContextValue = { user, ready, configured: firebaseConfigured, loginOpen, openLogin, closeLogin, signInWithGoogle, signOut, deleteAccount }

  return <AccountContext.Provider value={value}>{children}</AccountContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAccount() {
  const value = useContext(AccountContext)
  if (!value) throw new Error('AccountProvider가 필요합니다.')
  return value
}
