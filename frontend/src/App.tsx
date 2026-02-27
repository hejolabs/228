import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ClassGroups from './pages/ClassGroups'
import Students from './pages/Students'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/class-groups" element={<ClassGroups />} />
        <Route path="/students" element={<Students />} />
      </Route>
    </Routes>
  )
}
