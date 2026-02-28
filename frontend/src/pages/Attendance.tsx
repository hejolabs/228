import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
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

const DAY_MAP: Record<number, string> = {
  0: 'sun', 1: 'mon', 2: 'tue', 3: 'wed', 4: 'thu', 5: 'fri', 6: 'sat',
}

function getStatusBadge(status: string) {
  const opt = STATUS_OPTIONS.find((o) => o.value === status)
  return opt ? <span className={`px-2 py-0.5 rounded text-xs font-medium ${opt.color}`}>{opt.label}</span> : status
}

export default function Attendance() {
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([])
  const [selectedGroup, setSelectedGroup] = useState<string>('')
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

  // 수업반 선택 시 출석 기록 로드 (스케줄 기반 - 미리 생성된 레코드)
  useEffect(() => {
    if (!selectedGroup) return
    setLoading(true)
    fetch(`/api/attendance/daily/${date}?class_group_id=${selectedGroup}`)
      .then((r) => r.json())
      .then((data) => {
        setRecords(data)
        setLoading(false)
      })
  }, [selectedGroup, date])

  const handleStatusChange = async (record: AttendanceRecord, newStatus: string) => {
    const isExcused = newStatus === 'absent_excused'

    const res = await fetch(`/api/attendance/${record.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        status: newStatus,
        counts_toward_cycle: !isExcused,
        excuse_reason: isExcused ? 'sick_leave' : null,
      }),
    })
    const updated = await res.json()
    setRecords((prev) => prev.map((r) => r.id === record.id ? updated : r))
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
              <TableHead>회차</TableHead>
              <TableHead>출석 상태</TableHead>
              <TableHead>출석 체크</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {records.map((record) => (
              <TableRow key={record.id}>
                <TableCell className="font-medium">{record.student_name}</TableCell>
                <TableCell>
                  <span className={`font-mono font-bold ${record.current_count >= 7 ? 'text-destructive' : ''}`}>
                    {record.current_count}/{record.total_count}
                  </span>
                </TableCell>
                <TableCell>
                  {getStatusBadge(record.status)}
                </TableCell>
                <TableCell>
                  <div className="flex gap-1">
                    {STATUS_OPTIONS.map((opt) => (
                      <Button
                        key={opt.value}
                        size="sm"
                        variant={record.status === opt.value ? 'default' : 'outline'}
                        className="text-xs px-2 py-1 h-7"
                        onClick={() => handleStatusChange(record, opt.value)}
                      >
                        {opt.label}
                      </Button>
                    ))}
                  </div>
                </TableCell>
              </TableRow>
            ))}
            {records.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                  {selectedGroup ? '이 날짜에 스케줄이 없습니다.' : '수업반을 선택해주세요.'}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
