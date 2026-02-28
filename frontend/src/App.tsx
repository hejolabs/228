import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ClassGroups from './pages/ClassGroups'
import Students from './pages/Students'
import Enrollment from './pages/Enrollment'
import Attendance from './pages/Attendance'
import Payments from './pages/Payments'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/class-groups" element={<ClassGroups />} />
        <Route path="/students" element={<Students />} />
        <Route path="/enrollment" element={<Enrollment />} />
        <Route path="/attendance" element={<Attendance />} />
        <Route path="/payments" element={<Payments />} />
      </Route>
    </Routes>
  )
}
