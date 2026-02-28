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
  level_test_date: string | null
  level_test_time: string | null
  level_test_result: string | null
  inquiry_date: string | null
  level_test_status_date: string | null
  active_date: string | null
  stopped_date: string | null
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

const STATUS_TABS = [
  { key: 'inquiry', label: '문의', color: 'bg-blue-100 text-blue-800', activeColor: 'bg-blue-600 text-white' },
  { key: 'level_test', label: '레벨테스트', color: 'bg-yellow-100 text-yellow-800', activeColor: 'bg-yellow-500 text-white' },
  { key: 'active', label: '수업중', color: 'bg-green-100 text-green-800', activeColor: 'bg-green-600 text-white' },
  { key: 'stopped', label: '종료', color: 'bg-gray-100 text-gray-600', activeColor: 'bg-gray-600 text-white' },
] as const

const ENROLLMENT_STATUS: Record<string, { label: string; color: string }> = {
  inquiry: { label: '문의', color: 'bg-blue-100 text-blue-800' },
  level_test: { label: '레벨테스트', color: 'bg-yellow-100 text-yellow-800' },
  active: { label: '수업중', color: 'bg-green-100 text-green-800' },
  stopped: { label: '수업종료', color: 'bg-gray-100 text-gray-600' },
}

const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  inquiry: ['level_test', 'active', 'stopped'],
  level_test: ['active', 'stopped'],
  active: ['stopped'],
  stopped: ['active'],
}

export default function Enrollment() {
  const [activeTab, setActiveTab] = useState('inquiry')
  const [students, setStudents] = useState<Student[]>([])
  const [allStudents, setAllStudents] = useState<Student[]>([])
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([])

  // 상태 변경 다이얼로그
  const [statusOpen, setStatusOpen] = useState(false)
  const [statusTarget, setStatusTarget] = useState<Student | null>(null)
  const [nextStatus, setNextStatus] = useState('')
  const [statusMemo, setStatusMemo] = useState('')

  // 이력 다이얼로그
  const [historyOpen, setHistoryOpen] = useState(false)
  const [historyStudent, setHistoryStudent] = useState<Student | null>(null)
  const [history, setHistory] = useState<HistoryEntry[]>([])

  // 레벨테스트 다이얼로그
  const [ltOpen, setLtOpen] = useState(false)
  const [ltTarget, setLtTarget] = useState<Student | null>(null)
  const [ltForm, setLtForm] = useState({ date: '', time: '', result: '' })

  // 사이클 시작 다이얼로그
  const [cycleOpen, setCycleOpen] = useState(false)
  const [cycleStudent, setCycleStudent] = useState<Student | null>(null)
  const [cycleStartDate, setCycleStartDate] = useState('')

  // 신규 문의 등록 다이얼로그
  const [createOpen, setCreateOpen] = useState(false)
  const [createForm, setCreateForm] = useState({
    name: '', phone: '', school: '', grade: '', parent_phone: '',
    class_group_id: 0, memo: '',
  })

  const fetchAllStudents = async () => {
    const res = await fetch('/api/students?enrollment_status=all')
    const data: Student[] = await res.json()
    setAllStudents(data)
    setStudents(data.filter((s) => s.enrollment_status === activeTab))
  }

  const fetchClassGroups = async () => {
    const res = await fetch('/api/class-groups')
    setClassGroups(await res.json())
  }

  useEffect(() => { fetchClassGroups() }, [])
  useEffect(() => { fetchAllStudents() }, [])
  useEffect(() => {
    setStudents(allStudents.filter((s) => s.enrollment_status === activeTab))
  }, [activeTab, allStudents])

  const statusCount = (key: string) => allStudents.filter((s) => s.enrollment_status === key).length

  const gradeLabel = (grade: string) => GRADE_OPTIONS.find((g) => g.value === grade)?.label ?? grade
  const formatDate = (d: string | null) => d ? new Date(d).toLocaleDateString('ko-KR', { month: 'numeric', day: 'numeric' }) : '-'
  const formatTuition = (amount: number) => amount.toLocaleString() + '원'

  // 상태 변경
  const openStatusDialog = (s: Student, target?: string) => {
    const transitions = ALLOWED_TRANSITIONS[s.enrollment_status] ?? []
    if (transitions.length === 0) return
    setStatusTarget(s)
    setNextStatus(target ?? transitions[0])
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
      const updated: Student = await res.json()
      if (!updated.current_cycle) {
        setCycleStudent(updated)
        setCycleStartDate(new Date().toISOString().slice(0, 10))
        setCycleOpen(true)
      }
    }
    fetchAllStudents()
  }

  // 이력 보기
  const openHistory = async (s: Student) => {
    setHistoryStudent(s)
    const res = await fetch(`/api/students/${s.id}/history`)
    setHistory(await res.json())
    setHistoryOpen(true)
  }

  // 레벨테스트 일정/결과
  const openLevelTest = (s: Student) => {
    setLtTarget(s)
    setLtForm({
      date: s.level_test_date ?? '',
      time: s.level_test_time ?? '',
      result: s.level_test_result ?? '',
    })
    setLtOpen(true)
  }

  const handleLevelTestSave = async () => {
    if (!ltTarget) return
    const res = await fetch(`/api/students/${ltTarget.id}/level-test`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        level_test_date: ltForm.date || null,
        level_test_time: ltForm.time || null,
        level_test_result: ltForm.result || null,
      }),
    })
    if (!res.ok) {
      alert('저장 실패')
      return
    }
    setLtOpen(false)
    fetchAllStudents()
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
    fetchAllStudents()
  }

  // 신규 문의 등록
  const handleCreate = async () => {
    const res = await fetch('/api/students', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...createForm,
        class_group_id: createForm.class_group_id || classGroups[0]?.id,
        tuition_amount: null,
        enrollment_status: 'inquiry',
        memo: createForm.memo || null,
      }),
    })
    if (!res.ok) {
      alert('등록 실패')
      return
    }
    setCreateOpen(false)
    setCreateForm({ name: '', phone: '', school: '', grade: '', parent_phone: '', class_group_id: 0, memo: '' })
    setActiveTab('inquiry')
    fetchAllStudents()
  }

  // 다음 상태 버튼 텍스트
  const nextStatusButton = (s: Student): { label: string; target: string } | null => {
    const map: Record<string, { label: string; target: string }> = {
      inquiry: { label: '→ 레벨테스트', target: 'level_test' },
      level_test: { label: '→ 수업시작', target: 'active' },
      active: { label: '→ 수업종료', target: 'stopped' },
      stopped: { label: '→ 재등록', target: 'active' },
    }
    return map[s.enrollment_status] ?? null
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">수업등록 관리</h2>
        <Button onClick={() => setCreateOpen(true)}>+ 신규 문의</Button>
      </div>

      {/* 탭 */}
      <div className="flex gap-2 mb-4">
        {STATUS_TABS.map((tab) => {
          const count = statusCount(tab.key)
          const isActive = activeTab === tab.key
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive ? tab.activeColor : tab.color + ' hover:opacity-80'
              }`}
            >
              {tab.label} ({count})
            </button>
          )
        })}
      </div>

      {/* 테이블 */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>이름</TableHead>
            <TableHead>학년</TableHead>
            <TableHead>수업반</TableHead>
            {activeTab === 'inquiry' && <TableHead>문의일</TableHead>}
            {activeTab === 'inquiry' && <TableHead>학부모 연락처</TableHead>}
            {activeTab === 'level_test' && <TableHead>테스트 예정</TableHead>}
            {activeTab === 'level_test' && <TableHead>결과</TableHead>}
            {activeTab === 'active' && <TableHead>수업시작일</TableHead>}
            {activeTab === 'active' && <TableHead>회차</TableHead>}
            {activeTab === 'active' && <TableHead>수업료</TableHead>}
            {activeTab === 'stopped' && <TableHead>수업종료일</TableHead>}
            <TableHead className="text-right">관리</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {students.map((s) => {
            const btn = nextStatusButton(s)
            return (
              <TableRow key={s.id}>
                <TableCell className="font-medium">{s.name}</TableCell>
                <TableCell><Badge variant="secondary">{gradeLabel(s.grade)}</Badge></TableCell>
                <TableCell>{s.class_group_name ?? '-'}</TableCell>

                {/* 문의 탭 */}
                {activeTab === 'inquiry' && <TableCell>{formatDate(s.inquiry_date)}</TableCell>}
                {activeTab === 'inquiry' && <TableCell>{s.parent_phone}</TableCell>}

                {/* 레벨테스트 탭 */}
                {activeTab === 'level_test' && (
                  <TableCell>
                    {s.level_test_date ? (
                      <span>
                        {formatDate(s.level_test_date)}
                        {s.level_test_time && ` ${s.level_test_time}`}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">미정</span>
                    )}
                  </TableCell>
                )}
                {activeTab === 'level_test' && (
                  <TableCell>
                    {s.level_test_result ? (
                      <span className="text-xs">{s.level_test_result}</span>
                    ) : (
                      <span className="text-muted-foreground text-xs">미완료</span>
                    )}
                  </TableCell>
                )}

                {/* 수업중 탭 */}
                {activeTab === 'active' && <TableCell>{formatDate(s.active_date)}</TableCell>}
                {activeTab === 'active' && (
                  <TableCell>
                    {s.current_cycle ? (
                      <span className={s.current_cycle.current_count >= 7 ? 'text-destructive font-bold' : ''}>
                        {s.current_cycle.current_count}/{s.current_cycle.total_count}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                )}
                {activeTab === 'active' && <TableCell>{formatTuition(s.effective_tuition)}</TableCell>}

                {/* 종료 탭 */}
                {activeTab === 'stopped' && <TableCell>{formatDate(s.stopped_date)}</TableCell>}

                {/* 액션 */}
                <TableCell className="text-right">
                  <div className="flex gap-1 justify-end">
                    {activeTab === 'level_test' && (
                      <Button variant="outline" size="sm" className="text-xs" onClick={() => openLevelTest(s)}>
                        일정/결과
                      </Button>
                    )}
                    {btn && (
                      <Button variant="outline" size="sm" className="text-xs" onClick={() => openStatusDialog(s, btn.target)}>
                        {btn.label}
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" className="text-xs" onClick={() => openHistory(s)}>
                      이력
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            )
          })}
          {students.length === 0 && (
            <TableRow>
              <TableCell colSpan={10} className="text-center text-muted-foreground py-8">
                해당 상태의 학생이 없습니다.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

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

      {/* 레벨테스트 일정/결과 다이얼로그 */}
      <Dialog open={ltOpen} onOpenChange={setLtOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>레벨테스트 - {ltTarget?.name}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>예정일</Label>
                <Input
                  type="date"
                  value={ltForm.date}
                  onChange={(e) => setLtForm({ ...ltForm, date: e.target.value })}
                />
              </div>
              <div className="grid gap-2">
                <Label>시간</Label>
                <Input
                  type="time"
                  value={ltForm.time}
                  onChange={(e) => setLtForm({ ...ltForm, time: e.target.value })}
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>결과/메모</Label>
              <Input
                value={ltForm.result}
                onChange={(e) => setLtForm({ ...ltForm, result: e.target.value })}
                placeholder="테스트 결과를 입력하세요"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setLtOpen(false)}>취소</Button>
            <Button onClick={handleLevelTestSave}>저장</Button>
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

      {/* 신규 문의 등록 다이얼로그 */}
      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>신규 문의 등록</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>이름</Label>
                <Input value={createForm.name} onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })} />
              </div>
              <div className="grid gap-2">
                <Label>학교</Label>
                <Input value={createForm.school} onChange={(e) => setCreateForm({ ...createForm, school: e.target.value })} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>학년</Label>
                <Select value={createForm.grade} onValueChange={(v) => setCreateForm({ ...createForm, grade: v })}>
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
                <Select value={createForm.class_group_id ? String(createForm.class_group_id) : ''} onValueChange={(v) => setCreateForm({ ...createForm, class_group_id: Number(v) })}>
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
                <Input value={createForm.phone} onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })} placeholder="010-0000-0000" />
              </div>
              <div className="grid gap-2">
                <Label>학부모 연락처</Label>
                <Input value={createForm.parent_phone} onChange={(e) => setCreateForm({ ...createForm, parent_phone: e.target.value })} placeholder="010-0000-0000" />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>메모</Label>
              <Input value={createForm.memo} onChange={(e) => setCreateForm({ ...createForm, memo: e.target.value })} placeholder="문의 내용 메모" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateOpen(false)}>취소</Button>
            <Button onClick={handleCreate}>등록</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
