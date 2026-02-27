import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ClassGroups from './pages/ClassGroups'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/class-groups" element={<ClassGroups />} />
      </Route>
    </Routes>
  )
}
