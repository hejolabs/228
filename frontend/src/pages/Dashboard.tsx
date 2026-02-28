import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell, TableRow,
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

interface StatusCounts {
  inquiry: number
  level_test: number
  active: number
  stopped: number
}

const DAY_MAP: Record<number, string> = {
  0: 'sun', 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat',
}

export default function Dashboard() {
  const [todayGroups, setTodayGroups] = useState<ClassGroup[]>([])
  const [alerts, setAlerts] = useState<CycleAlert[]>([])
  const [statusCounts, setStatusCounts] = useState<StatusCounts>({ inquiry: 0, level_test: 0, active: 0, stopped: 0 })
  const [pendingCount, setPendingCount] = useState(0)

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

    // 상태별 학생 수
    Promise.all([
      fetch('/api/students?enrollment_status=inquiry').then((r) => r.json()),
      fetch('/api/students?enrollment_status=level_test').then((r) => r.json()),
      fetch('/api/students?enrollment_status=active').then((r) => r.json()),
      fetch('/api/students?enrollment_status=stopped').then((r) => r.json()),
    ]).then(([inq, lt, act, stp]) => {
      setStatusCounts({
        inquiry: inq.length,
        level_test: lt.length,
        active: act.length,
        stopped: stp.length,
      })
    })

    // 미납 건수
    fetch('/api/payments?status=pending')
      .then((r) => r.json())
      .then((payments) => setPendingCount(payments.length))
  }, [])

  const completedAlerts = alerts.filter((a) => a.status === 'completed')

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">대시보드</h2>

      {/* 학생 현황 카드 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div className="border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-blue-600">{statusCounts.inquiry}</p>
          <p className="text-sm text-muted-foreground">문의</p>
        </div>
        <div className="border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-yellow-600">{statusCounts.level_test}</p>
          <p className="text-sm text-muted-foreground">레벨테스트</p>
        </div>
        <div className="border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-green-600">{statusCounts.active}</p>
          <p className="text-sm text-muted-foreground">수업중</p>
        </div>
        <div className="border rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-gray-500">{statusCounts.stopped}</p>
          <p className="text-sm text-muted-foreground">수업종료</p>
        </div>
      </div>

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
            사이클 완료 (납부 대기)
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
          <Link to="/payments">
            <Button variant="outline" size="sm" className="mt-3 w-full">수업료 관리로 이동</Button>
          </Link>
        </div>

        {/* 미납 현황 */}
        <div className="border rounded-lg p-4">
          <h3 className="font-semibold mb-3">
            미납 현황
            {pendingCount > 0 && (
              <Badge variant="destructive" className="ml-2">{pendingCount}건</Badge>
            )}
          </h3>
          {pendingCount > 0 ? (
            <p className="text-sm">미납 <span className="font-bold text-destructive">{pendingCount}건</span>이 있습니다.</p>
          ) : (
            <p className="text-muted-foreground text-sm">미납 내역이 없습니다.</p>
          )}
          <Link to="/payments">
            <Button variant="outline" size="sm" className="mt-3 w-full">수업료 관리로 이동</Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
