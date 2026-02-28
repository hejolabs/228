import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'

interface ClassGroup {
  id: number
  name: string
}

interface Cycle {
  id: number
  cycle_number: number
  current_count: number
  total_count: number
  status: string
}

interface Student {
  id: number
  name: string
  phone: string
  school: string
  grade: string
  parent_phone: string
  class_group_id: number
  class_group_name: string | null
  tuition_amount: number | null
  effective_tuition: number
  enrollment_status: string
  current_cycle: Cycle | null
  memo: string | null
}

interface GradeConfig {
  label: string
  duration_minutes: number
  tuition: number
}

interface HistoryEntry {
  id: number
  from_status: string | null
  to_status: string
  changed_at: string
  memo: string | null
}

const GRADE_OPTIONS = [
  { value: 'elementary', label: '초등' },
  { value: 'middle1', label: '중1' },
  { value: 'middle2', label: '중2' },
  { value: 'middle3', label: '중3' },
  { value: 'high', label: '고등' },
]

const ENROLLMENT_STATUS = {
  inquiry: { label: '문의', color: 'bg-blue-100 text-blue-800' },
  level_test: { label: '레벨테스트', color: 'bg-yellow-100 text-yellow-800' },
  active: { label: '수업중', color: 'bg-green-100 text-green-800' },
  stopped: { label: '수업종료', color: 'bg-gray-100 text-gray-600' },
} as Record<string, { label: string; color: string }>

const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  inquiry: ['level_test', 'active', 'stopped'],
  level_test: ['active', 'stopped'],
  active: ['stopped'],
  stopped: ['active'],
}

const EMPTY_FORM = {
  name: '',
  phone: '',
  school: '',
  grade: '',
  parent_phone: '',
  class_group_id: 0,
  tuition_amount: '' as string | number,
  memo: '',
  enrollment_status: 'inquiry',
}

export default function Students() {
  const [students, setStudents] = useState<Student[]>([])
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([])
  const [grades, setGrades] = useState<Record<string, GradeConfig>>({})
  const [filterGroup, setFilterGroup] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [open, setOpen] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [form, setForm] = useState(EMPTY_FORM)

  // 상태 변경 다이얼로그
  const [statusOpen, setStatusOpen] = useState(false)
  const [statusTarget, setStatusTarget] = useState<Student | null>(null)
  const [nextStatus, setNextStatus] = useState('')
  const [statusMemo, setStatusMemo] = useState('')

  // 이력 다이얼로그
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyStudent, setHistoryStudent] = useState<Student | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])

  // 사이클 시작 다이얼로그
  const [cycleOpen, setCycleOpen] = useState(false)
  const [cycleStudent, setCycleStudent] = useState<Student | null>(null)
  const [cycleStartDate, setCycleStartDate] = useState('')

  const fetchStudents = async () => {
    let url = '/api/students'
    const params: string[] = []
    if (filterGroup !== 'all') params.push(`class_group_id=${filterGroup}`)
    if (filterStatus !== 'all') params.push(`enrollment_status=${filterStatus}`)
    if (params.length > 0) url += '?' + params.join('&')
    const res = await fetch(url)
    setStudents(await res.json())
  }

  const fetchClassGroups = async () => {
    const res = await fetch('/api/class-groups')
    setClassGroups(await res.json())
  }

  const fetchGrades = async () => {
    const res = await fetch('/api/grades')
    setGrades(await res.json())
  }

  useEffect(() => { fetchClassGroups(); fetchGrades() }, [])
  useEffect(() => { fetchStudents() }, [filterGroup, filterStatus])

  const gradeLabel = (grade: string) => GRADE_OPTIONS.find((g) => g.value === grade)?.label ?? grade

  const formatTuition = (amount: number) => amount.toLocaleString() + '원'

  const openCreate = () => {
    setEditId(null)
    setForm(EMPTY_FORM)
    setOpen(true)
  }

  const openEdit = (s: Student) => {
    setEditId(s.id)
    setForm({
      name: s.name,
      phone: s.phone,
      school: s.school,
      grade: s.grade,
      parent_phone: s.parent_phone,
      class_group_id: s.class_group_id,
      tuition_amount: s.tuition_amount ?? '',
      memo: s.memo ?? '',
      enrollment_status: s.enrollment_status,
    })
    setOpen(true)
  }

  const selectedGradeTuition = form.grade && grades[form.grade] ? grades[form.grade].tuition : null

  const handleSubmit = async () => {
    const body: Record<string, unknown> = {
      ...form,
      tuition_amount: form.tuition_amount === '' ? null : Number(form.tuition_amount),
      memo: form.memo || null,
    }
    if (editId) {
      // 수정 시 enrollment_status는 별도 API로 변경
      delete body.enrollment_status
      await fetch(`/api/students/${editId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    } else {
      await fetch('/api/students', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    }
    setOpen(false)
    fetchStudents()
  }

  const handleDelete = async (id: number) => {
    if (!confirm('정말 삭제(수업종료)하시겠습니까?')) return
    await fetch(`/api/students/${id}`, { method: 'DELETE' })
    fetchStudents()
  }

  // 상태 변경
  const openStatusDialog = (s: Student) => {
    const transitions = ALLOWED_TRANSITIONS[s.enrollment_status] ?? []
    if (transitions.length === 0) return
    setStatusTarget(s)
    setNextStatus(transitions[0])
    setStatusMemo('')
    setStatusOpen(true)
  }

  const handleStatusChange = async () => {
    if (!statusTarget) return
    const res = await fetch(`/api/students/${statusTarget.id}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: nextStatus, memo: statusMemo || null }),
    })
    if (!res.ok) {
      const err = await res.json()
      alert(err.detail || '상태 변경 실패')
      return
    }
    setStatusOpen(false)

    // active로 변경 시 사이클 시작 제안
    if (nextStatus === 'active') {
      const updated = await res.json()
      if (!updated.current_cycle) {
        setCycleStudent(updated)
        setCycleStartDate(new Date().toISOString().slice(0, 10))
        setCycleOpen(true)
      }
    }
    fetchStudents()
  }

  // 이력 보기
  const openHistory = async (s: Student) => {
    setHistoryStudent(s)
    const res = await fetch(`/api/students/${s.id}/history`)
    setHistory(await res.json())
    setHistoryOpen(true)
  }

  // 사이클 시작
  const handleStartCycle = async () => {
    if (!cycleStudent) return
    const res = await fetch(`/api/students/${cycleStudent.id}/start-cycle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start_date: cycleStartDate }),
    })
    if (!res.ok) {
      const err = await res.json()
      alert(err.detail || '사이클 시작 실패')
      return
    }
    setCycleOpen(false)
    fetchStudents()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">학생 관리</h2>
        <Button onClick={openCreate}>+ 학생 등록</Button>
      </div>

      {/* 필터 */}
      <div className="flex gap-3 mb-4">
        <Select value={filterGroup} onValueChange={setFilterGroup}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="수업반 필터" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">전체 수업반</SelectItem>
            {classGroups.map((g) => (
              <SelectItem key={g.id} value={String(g.id)}>{g.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={filterStatus} onValueChange={setFilterStatus}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="상태 필터" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">전체 상태</SelectItem>
            {Object.entries(ENROLLMENT_STATUS).map(([key, val]) => (
              <SelectItem key={key} value={key}>{val.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>이름</TableHead>
            <TableHead>상태</TableHead>
            <TableHead>학교</TableHead>
            <TableHead>학년</TableHead>
            <TableHead>수업반</TableHead>
            <TableHead>회차</TableHead>
            <TableHead>수업료</TableHead>
            <TableHead>학부모 연락처</TableHead>
            <TableHead className="text-right">관리</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.map((s) => {
            const statusInfo = ENROLLMENT_STATUS[s.enrollment_status] ?? { label: s.enrollment_status, color: '' }
            const transitions = ALLOWED_TRANSITIONS[s.enrollment_status] ?? []

            return (
              <TableRow key={s.id}>
                <TableCell className="font-medium">{s.name}</TableCell>
                <TableCell>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusInfo.color}`}>
                    {statusInfo.label}
                  </span>
                </TableCell>
                <TableCell>{s.school}</TableCell>
                <TableCell><Badge variant="secondary">{gradeLabel(s.grade)}</Badge></TableCell>
                <TableCell>{s.class_group_name}</TableCell>
                <TableCell>
                  {s.current_cycle ? (
                    <span className={s.current_cycle.current_count >= 7 ? 'text-destructive font-bold' : ''}>
                      {s.current_cycle.current_count}/{s.current_cycle.total_count}
                    </span>
                  ) : '-'}
                </TableCell>
                <TableCell>{formatTuition(s.effective_tuition)}</TableCell>
                <TableCell>{s.parent_phone}</TableCell>
                <TableCell className="text-right">
                  <div className="flex gap-1 justify-end">
                    {transitions.length > 0 && (
                      <Button variant="outline" size="sm" className="text-xs" onClick={() => openStatusDialog(s)}>
                        상태변경
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" className="text-xs" onClick={() => openHistory(s)}>
                      이력
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => openEdit(s)}>수정</Button>
                    {s.enrollment_status !== 'stopped' && (
                      <Button variant="ghost" size="sm" className="text-destructive" onClick={() => handleDelete(s.id)}>삭제</Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            )
          })}
          {students.length === 0 && (
            <TableRow>
              <TableCell colSpan={9} className="text-center text-muted-foreground py-8">
                등록된 학생이 없습니다.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

      {/* 학생 등록/수정 다이얼로그 */}
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editId ? '학생 수정' : '학생 등록'}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>이름</Label>
                <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="grid gap-2">
                <Label>학교</Label>
                <Input value={form.school} onChange={(e) => setForm({ ...form, school: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>학년</Label>
                <Select value={form.grade} onValueChange={(v) => setForm({ ...form, grade: v })}>
                  <SelectTrigger><SelectValue placeholder="학년 선택" /></SelectTrigger>
                  <SelectContent>
                    {GRADE_OPTIONS.map((g) => (
                      <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>수업반</Label>
                <Select value={form.class_group_id ? String(form.class_group_id) : ''} onValueChange={(v) => setForm({ ...form, class_group_id: Number(v) })}>
                  <SelectTrigger><SelectValue placeholder="수업반 선택" /></SelectTrigger>
                  <SelectContent>
                    {classGroups.map((g) => (
                      <SelectItem key={g.id} value={String(g.id)}>{g.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>학생 연락처</Label>
                <Input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="010-0000-0000" />
              </div>
              <div className="grid gap-2">
                <Label>학부모 연락처</Label>
                <Input value={form.parent_phone} onChange={(e) => setForm({ ...form, parent_phone: e.target.value })} placeholder="010-0000-0000" />
              </div>
            </div>
            {!editId && (
              <div className="grid gap-2">
                <Label>등록 상태</Label>
                <Select value={form.enrollment_status} onValueChange={(v) => setForm({ ...form, enrollment_status: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(ENROLLMENT_STATUS).map(([key, val]) => (
                      <SelectItem key={key} value={key}>{val.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            <div className="grid gap-2">
              <Label>
                수업료 (개별)
                {selectedGradeTuition && (
                  <span className="text-muted-foreground ml-2">
                    기본: {selectedGradeTuition.toLocaleString()}원
                  </span>
                )}
              </Label>
              <Input
                type="number"
                value={form.tuition_amount}
                onChange={(e) => setForm({ ...form, tuition_amount: e.target.value })}
                placeholder={selectedGradeTuition ? `비워두면 기본 ${selectedGradeTuition.toLocaleString()}원 적용` : '학년을 먼저 선택하세요'}
              />
            </div>
            <div className="grid gap-2">
              <Label>메모</Label>
              <Input value={form.memo} onChange={(e) => setForm({ ...form, memo: e.target.value })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>취소</Button>
            <Button onClick={handleSubmit}>{editId ? '수정' : '등록'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 상태 변경 다이얼로그 */}
      <Dialog open={statusOpen} onOpenChange={setStatusOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>상태 변경 - {statusTarget?.name}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex items-center gap-2 text-sm">
              <span className={`px-2 py-0.5 rounded font-medium ${ENROLLMENT_STATUS[statusTarget?.enrollment_status ?? '']?.color ?? ''}`}>
                {ENROLLMENT_STATUS[statusTarget?.enrollment_status ?? '']?.label}
              </span>
              <span>→</span>
              <Select value={nextStatus} onValueChange={setNextStatus}>
                <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {(ALLOWED_TRANSITIONS[statusTarget?.enrollment_status ?? ''] ?? []).map((s) => (
                    <SelectItem key={s} value={s}>{ENROLLMENT_STATUS[s]?.label ?? s}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>메모 (선택)</Label>
              <Input
                value={statusMemo}
                onChange={(e) => setStatusMemo(e.target.value)}
                placeholder="변경 사유를 입력하세요"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setStatusOpen(false)}>취소</Button>
            <Button onClick={handleStatusChange}>변경</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 이력 다이얼로그 */}
      <Dialog open={historyOpen} onOpenChange={setHistoryOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>상태 변경 이력 - {historyStudent?.name}</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            {history.length > 0 ? (
              <div className="space-y-3">
                {history.map((h) => (
                  <div key={h.id} className="flex items-center gap-2 text-sm border-b pb-2">
                    <span className="text-muted-foreground w-28 shrink-0">
                      {new Date(h.changed_at).toLocaleDateString('ko-KR')}
                    </span>
                    {h.from_status ? (
                      <>
                        <span className={`px-1.5 py-0.5 rounded text-xs ${ENROLLMENT_STATUS[h.from_status]?.color ?? ''}`}>
                          {ENROLLMENT_STATUS[h.from_status]?.label ?? h.from_status}
                        </span>
                        <span>→</span>
                      </>
                    ) : (
                      <span className="text-muted-foreground text-xs">등록 →</span>
                    )}
                    <span className={`px-1.5 py-0.5 rounded text-xs ${ENROLLMENT_STATUS[h.to_status]?.color ?? ''}`}>
                      {ENROLLMENT_STATUS[h.to_status]?.label ?? h.to_status}
                    </span>
                    {h.memo && (
                      <span className="text-muted-foreground ml-2">({h.memo})</span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">이력이 없습니다.</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setHistoryOpen(false)}>닫기</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 사이클 시작 다이얼로그 */}
      <Dialog open={cycleOpen} onOpenChange={setCycleOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>첫 사이클 시작 - {cycleStudent?.name}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <p className="text-sm text-muted-foreground">
              수업 시작일을 선택하면 8회차 스케줄이 자동 생성됩니다.
            </p>
            <div className="grid gap-2">
              <Label>수업 시작일</Label>
              <Input
                type="date"
                value={cycleStartDate}
                onChange={(e) => setCycleStartDate(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCycleOpen(false)}>나중에</Button>
            <Button onClick={handleStartCycle}>시작</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
