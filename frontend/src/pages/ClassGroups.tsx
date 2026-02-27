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
import { formatDays } from '@/lib/utils'

interface ClassGroup {
  id: number
  name: string
  days_of_week: string[]
  start_time: string
  default_duration_minutes: number
  memo: string | null
  is_active: boolean
}

const ALL_DAYS = [
  { value: 'mon', label: '월' },
  { value: 'tue', label: '화' },
  { value: 'wed', label: '수' },
  { value: 'thu', label: '목' },
  { value: 'fri', label: '금' },
  { value: 'sat', label: '토' },
  { value: 'sun', label: '일' },
]

const EMPTY_FORM = {
  name: '',
  days_of_week: [] as string[],
  start_time: '',
  default_duration_minutes: 90,
  memo: '',
}

export default function ClassGroups() {
  const [groups, setGroups] = useState<ClassGroup[]>([])
  const [open, setOpen] = useState(false)
  const [editId, setEditId] = useState<number | null>(null)
  const [form, setForm] = useState(EMPTY_FORM)

  const fetchGroups = async () => {
    const res = await fetch('/api/class-groups')
    setGroups(await res.json())
  }

  useEffect(() => { fetchGroups() }, [])

  const openCreate = () => {
    setEditId(null)
    setForm(EMPTY_FORM)
    setOpen(true)
  }

  const openEdit = (g: ClassGroup) => {
    setEditId(g.id)
    setForm({
      name: g.name,
      days_of_week: g.days_of_week,
      start_time: g.start_time,
      default_duration_minutes: g.default_duration_minutes,
      memo: g.memo ?? '',
    })
    setOpen(true)
  }

  const toggleDay = (day: string) => {
    setForm((f) => ({
      ...f,
      days_of_week: f.days_of_week.includes(day)
        ? f.days_of_week.filter((d) => d !== day)
        : [...f.days_of_week, day],
    }))
  }

  const handleSubmit = async () => {
    const body = { ...form, memo: form.memo || null }
    if (editId) {
      await fetch(`/api/class-groups/${editId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    } else {
      await fetch('/api/class-groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    }
    setOpen(false)
    fetchGroups()
  }

  const handleDelete = async (id: number) => {
    if (!confirm('정말 삭제하시겠습니까?')) return
    await fetch(`/api/class-groups/${id}`, { method: 'DELETE' })
    fetchGroups()
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">수업반 관리</h2>
        <Button onClick={openCreate}>+ 수업반 추가</Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>수업반명</TableHead>
            <TableHead>요일</TableHead>
            <TableHead>시작 시간</TableHead>
            <TableHead>수업 시간</TableHead>
            <TableHead>메모</TableHead>
            <TableHead className="text-right">관리</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {groups.map((g) => (
            <TableRow key={g.id}>
              <TableCell className="font-medium">{g.name}</TableCell>
              <TableCell>
                <div className="flex gap-1">
                  {g.days_of_week.map((d) => (
                    <Badge key={d} variant="secondary">{formatDays([d])}</Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell>{g.start_time}</TableCell>
              <TableCell>{g.default_duration_minutes}분</TableCell>
              <TableCell className="text-muted-foreground">{g.memo}</TableCell>
              <TableCell className="text-right">
                <Button variant="ghost" size="sm" onClick={() => openEdit(g)}>수정</Button>
                <Button variant="ghost" size="sm" className="text-destructive" onClick={() => handleDelete(g.id)}>삭제</Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editId ? '수업반 수정' : '수업반 추가'}</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>수업반명</Label>
              <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="예: 월수반A" />
            </div>
            <div className="grid gap-2">
              <Label>수업 요일</Label>
              <div className="flex gap-2">
                {ALL_DAYS.map((d) => (
                  <Button
                    key={d.value}
                    type="button"
                    size="sm"
                    variant={form.days_of_week.includes(d.value) ? 'default' : 'outline'}
                    onClick={() => toggleDay(d.value)}
                  >
                    {d.label}
                  </Button>
                ))}
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label>시작 시간</Label>
                <Input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
              </div>
              <div className="grid gap-2">
                <Label>수업 시간 (분)</Label>
                <Input type="number" value={form.default_duration_minutes} onChange={(e) => setForm({ ...form, default_duration_minutes: Number(e.target.value) })} />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>메모</Label>
              <Input value={form.memo} onChange={(e) => setForm({ ...form, memo: e.target.value })} placeholder="비고" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>취소</Button>
            <Button onClick={handleSubmit}>{editId ? '수정' : '추가'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
