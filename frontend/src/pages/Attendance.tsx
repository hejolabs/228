import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface ClassGroup {
  id: number
  name: string
  days_of_week: string[]
}

interface Cycle {
  id: number
  current_count: number
  total_count: number
  status: string
}

interface Student {
  id: number
  name: string
  grade: string
  class_group_id: number
  class_group_name: string | null
  current_cycle: Cycle | null
}

interface AttendanceRecord {
  id: number
  student_id: number
  date: string
  status: string
  counts_toward_cycle: boolean
  excuse_reason: string | null
  student_name: string | null
  current_count: number
  total_count: number
}

const STATUS_OPTIONS = [
  { value: 'present', label: '출석', color: 'bg-green-100 text-green-800' },
  { value: 'late', label: '지각', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'early_leave', label: '조퇴', color: 'bg-orange-100 text-orange-800' },
  { value: 'absent', label: '결석', color: 'bg-red-100 text-red-800' },
  { value: 'absent_excused', label: '결석(미차감)', color: 'bg-gray-100 text-gray-800' },
]

const EXCUSE_OPTIONS = [
  { value: 'school_event', label: '학교행사' },
  { value: 'sick_leave', label: '병결' },
  { value: 'class_cancelled', label: '휴강' },
]

const DAY_MAP: Record<number, string> = {
  0: 'sun', 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat',
}

const GRADE_LABELS: Record<string, string> = {
  elementary: '초등', middle1: '중1', middle2: '중2', middle3: '중3', high: '고등',
}

function getStatusBadge(status: string) {
  const opt = STATUS_OPTIONS.find((o) => o.value === status)
  return opt ? <span className={`px-2 py-0.5 rounded text-xs font-medium ${opt.color}`}>{opt.label}</span> : status
}

export default function Attendance() {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([])
  const [selectedGroup, setSelectedGroup] = useState<string>('')
  const [students, setStudents] = useState<Student[]>([])
  const [records, setRecords] = useState<AttendanceRecord[]>([])
  const [loading, setLoading] = useState(false)

  // 수업반 목록
  useEffect(() => {
    fetch('/api/class-groups').then((r) => r.json()).then(setClassGroups)
  }, [])

  // 날짜 변경 시 요일에 해당하는 수업반 자동 선택
  useEffect(() => {
    if (classGroups.length === 0) return
    const dayOfWeek = DAY_MAP[new Date(date).getDay()]
    const matched = classGroups.filter((g) => g.days_of_week.includes(dayOfWeek))
    if (matched.length > 0 && !selectedGroup) {
      setSelectedGroup(String(matched[0].id))
    }
  }, [date, classGroups])

  // 수업반 선택 시 학생 + 출석 기록 로드
  useEffect(() => {
    if (!selectedGroup) return
    setLoading(true)
    Promise.all([
      fetch(`/api/students?class_group_id=${selectedGroup}`).then((r) => r.json()),
      fetch(`/api/attendance/daily/${date}?class_group_id=${selectedGroup}`).then((r) => r.json()),
    ]).then(([s, a]) => {
      setStudents(s)
      setRecords(a)
      setLoading(false)
    })
  }, [selectedGroup, date])

  const getRecord = (studentId: number) => records.find((r) => r.student_id === studentId)

  const handleAttendance = async (studentId: number, status: string) => {
    const existing = getRecord(studentId)
    const isExcused = status === 'absent_excused'

    if (existing) {
      // 수정
      const res = await fetch(`/api/attendance/${existing.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status,
          counts_toward_cycle: !isExcused,
          excuse_reason: isExcused ? 'sick_leave' : null,
        }),
      })
      const updated = await res.json()
      setRecords((prev) => prev.map((r) => r.id === existing.id ? updated : r))
    } else {
      // 신규
      const res = await fetch('/api/attendance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          date,
          status,
          counts_toward_cycle: !isExcused,
          excuse_reason: isExcused ? 'sick_leave' : null,
        }),
      })
      const created = await res.json()
      setRecords((prev) => [...prev, created])
    }

    // 학생 목록도 갱신 (사이클 카운트 반영)
    const studentsRes = await fetch(`/api/students?class_group_id=${selectedGroup}`)
    setStudents(await studentsRes.json())
  }

  const handleDelete = async (attId: number) => {
    await fetch(`/api/attendance/${attId}`, { method: 'DELETE' })
    setRecords((prev) => prev.filter((r) => r.id !== attId))
    const studentsRes = await fetch(`/api/students?class_group_id=${selectedGroup}`)
    setStudents(await studentsRes.json())
  }

  // 요일 기반 수업반 필터
  const dayOfWeek = DAY_MAP[new Date(date).getDay()]
  const todayGroups = classGroups.filter((g) => g.days_of_week.includes(dayOfWeek))

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">출석 관리</h2>

      <div className="flex gap-4 mb-4 items-end">
        <div className="grid gap-2">
          <Label>날짜</Label>
          <Input
            type="date"
            value={date}
            onChange={(e) => { setDate(e.target.value); setSelectedGroup('') }}
            className="w-44"
          />
        </div>
        <div className="grid gap-2">
          <Label>수업반</Label>
          <Select value={selectedGroup} onValueChange={setSelectedGroup}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder="수업반 선택" />
            </SelectTrigger>
            <SelectContent>
              {todayGroups.length > 0 ? (
                todayGroups.map((g) => (
                  <SelectItem key={g.id} value={String(g.id)}>{g.name}</SelectItem>
                ))
              ) : (
                classGroups.map((g) => (
                  <SelectItem key={g.id} value={String(g.id)}>{g.name}</SelectItem>
                ))
              )}
            </SelectContent>
          </Select>
        </div>
        {todayGroups.length === 0 && (
          <p className="text-sm text-muted-foreground pb-2">이 날짜에 해당하는 수업반이 없습니다.</p>
        )}
      </div>

      {loading ? (
        <p className="text-muted-foreground">로딩 중...</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>이름</TableHead>
              <TableHead>학년</TableHead>
              <TableHead>회차</TableHead>
              <TableHead>출석 상태</TableHead>
              <TableHead>출석 체크</TableHead>
              <TableHead className="text-right">취소</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {students.map((s) => {
              const record = getRecord(s.id)
              const cycle = s.current_cycle
              const isNearComplete = cycle && cycle.current_count >= 7

              return (
                <TableRow key={s.id} className={isNearComplete ? 'bg-red-50' : ''}>
                  <TableCell className="font-medium">{s.name}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{GRADE_LABELS[s.grade] ?? s.grade}</Badge>
                  </TableCell>
                  <TableCell>
                    {cycle ? (
                      <span className={`font-mono font-bold ${isNearComplete ? 'text-destructive' : ''}`}>
                        {cycle.current_count}/{cycle.total_count}
                      </span>
                    ) : '-'}
                  </TableCell>
                  <TableCell>
                    {record ? getStatusBadge(record.status) : <span className="text-muted-foreground text-sm">미처리</span>}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      {STATUS_OPTIONS.map((opt) => (
                        <Button
                          key={opt.value}
                          size="sm"
                          variant={record?.status === opt.value ? 'default' : 'outline'}
                          className="text-xs px-2 py-1 h-7"
                          onClick={() => handleAttendance(s.id, opt.value)}
                        >
                          {opt.label}
                        </Button>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    {record && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive text-xs"
                        onClick={() => handleDelete(record.id)}
                      >
                        취소
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              )
            })}
            {students.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                  {selectedGroup ? '이 수업반에 학생이 없습니다.' : '수업반을 선택해주세요.'}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
