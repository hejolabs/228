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
  current_cycle: Cycle | null
  memo: string | null
}

interface GradeConfig {
  label: string
  duration_minutes: number
  tuition: number
}

const GRADE_OPTIONS = [
  { value: 'elementary', label: '초등' },
  { value: 'middle1', label: '중1' },
  { value: 'middle2', label: '중2' },
  { value: 'middle3', label: '중3' },
  { value: 'high', label: '고등' },
]

const EMPTY_FORM = {
  name: '',
  phone: '',
  school: '',
  grade: '',
  parent_phone: '',
  class_group_id: 0,
  tuition_amount: '' as string | number,
  memo: '',
}

export default function Students() {
  const [students, setStudents] = useState<Student[]>([])
  const [classGroups, setClassGroups] = useState<ClassGroup[]>([])
  const [grades, setGrades] = useState<Record<string, GradeConfig>>({})
  const [filterGroup, setFilterGroup] = useState<string>('all')
  const [open, setOpen] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [form, setForm] = useState(EMPTY_FORM)

  const fetchStudents = async () => {
    const url = filterGroup === 'all' ? '/api/students' : `/api/students?class_group_id=${filterGroup}`
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
  useEffect(() => { fetchStudents() }, [filterGroup])

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
    })
    setOpen(true)
  }

  const selectedGradeTuition = form.grade && grades[form.grade] ? grades[form.grade].tuition : null

  const handleSubmit = async () => {
    const body = {
      ...form,
      tuition_amount: form.tuition_amount === '' ? null : Number(form.tuition_amount),
      memo: form.memo || null,
    }
    if (editId) {
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
    if (!confirm('정말 삭제하시겠습니까?')) return
    await fetch(`/api/students/${id}`, { method: 'DELETE' })
    fetchStudents()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">학생 관리</h2>
        <Button onClick={openCreate}>+ 학생 등록</Button>
      </div>

      <div className="mb-4">
        <Select value={filterGroup} onValueChange={setFilterGroup}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="수업반 필터" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">전체</SelectItem>
            {classGroups.map((g) => (
              <SelectItem key={g.id} value={String(g.id)}>{g.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>이름</TableHead>
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
          {students.map((s) => (
            <TableRow key={s.id}>
              <TableCell className="font-medium">{s.name}</TableCell>
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
                <Button variant="ghost" size="sm" onClick={() => openEdit(s)}>수정</Button>
                <Button variant="ghost" size="sm" className="text-destructive" onClick={() => handleDelete(s.id)}>삭제</Button>
              </TableCell>
            </TableRow>
          ))}
          {students.length === 0 && (
            <TableRow>
              <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                등록된 학생이 없습니다.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>

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
    </div>
  )
}
