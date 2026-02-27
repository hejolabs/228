import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'

interface ClassGroup {
  id: number
  name: string
  days_of_week: string[]
  start_time: string
  default_duration_minutes: number
}

interface CycleAlert {
  student_id: number
  student_name: string
  class_group_name: string
  cycle_id: number
  cycle_number: number
  current_count: number
  total_count: number
  status: string
}

const DAY_MAP: Record<number, string> = {
  0: 'sun', 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat',
}

const DAY_LABELS: Record<string, string> = {
  mon: '월', tue: '화', wed: '수', thu: '목', fri: '금', sat: '토', sun: '일',
}

export default function Dashboard() {
  const [todayGroups, setTodayGroups] = useState<ClassGroup[]>([])
  const [alerts, setAlerts] = useState<CycleAlert[]>([])

  useEffect(() => {
    const today = DAY_MAP[new Date().getDay()]

    fetch('/api/class-groups')
      .then((r) => r.json())
      .then((groups: ClassGroup[]) => {
        setTodayGroups(groups.filter((g) => g.days_of_week.includes(today)))
      })

    fetch('/api/cycles/alerts')
      .then((r) => r.json())
      .then(setAlerts)
  }, [])

  const completedAlerts = alerts.filter((a) => a.status === 'completed')
  const nearAlerts = alerts.filter((a) => a.status === 'in_progress')

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">대시보드</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 오늘의 수업 */}
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold mb-3">오늘의 수업</h3>
          {todayGroups.length > 0 ? (
            <div className="space-y-2">
              {todayGroups.map((g) => (
                <div key={g.id} className="flex items-center justify-between p-2 bg-secondary rounded">
                  <span className="font-medium">{g.name}</span>
                  <span className="text-sm text-muted-foreground">
                    {g.start_time} / {g.default_duration_minutes}분
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">오늘은 수업이 없습니다.</p>
          )}
          <Link to="/attendance">
            <Button variant="outline" size="sm" className="mt-3 w-full">출석 관리로 이동</Button>
          </Link>
        </div>

        {/* 사이클 완료 알림 */}
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold mb-3">
            사이클 완료
            {completedAlerts.length > 0 && (
              <Badge variant="destructive" className="ml-2">{completedAlerts.length}</Badge>
            )}
          </h3>
          {completedAlerts.length > 0 ? (
            <Table>
              <TableBody>
                {completedAlerts.map((a) => (
                  <TableRow key={a.cycle_id}>
                    <TableCell className="font-medium">{a.student_name}</TableCell>
                    <TableCell>{a.class_group_name}</TableCell>
                    <TableCell>
                      <Badge variant="destructive">{a.current_count}/{a.total_count}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-muted-foreground text-sm">완료된 사이클이 없습니다.</p>
          )}
        </div>

        {/* 사이클 임박 */}
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold mb-3">
            사이클 임박 (7/8 이상)
            {nearAlerts.length > 0 && (
              <Badge variant="secondary" className="ml-2">{nearAlerts.length}</Badge>
            )}
          </h3>
          {nearAlerts.length > 0 ? (
            <Table>
              <TableBody>
                {nearAlerts.map((a) => (
                  <TableRow key={a.cycle_id}>
                    <TableCell className="font-medium">{a.student_name}</TableCell>
                    <TableCell>{a.class_group_name}</TableCell>
                    <TableCell>
                      <span className="font-mono font-bold text-orange-600">
                        {a.current_count}/{a.total_count}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-muted-foreground text-sm">임박한 사이클이 없습니다.</p>
          )}
        </div>
      </div>
    </div>
  )
}
