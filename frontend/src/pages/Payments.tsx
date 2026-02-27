import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface Payment {
  id: number
  student_id: number
  cycle_id: number
  amount: number
  payment_method: string | null
  status: string
  message_sent: boolean
  message_sent_at: string | null
  paid_at: string | null
  memo: string | null
  created_at: string
  student_name: string | null
  class_group_name: string | null
  cycle_number: number
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: '미납', color: 'bg-red-100 text-red-800' },
  paid: { label: '납부완료', color: 'bg-green-100 text-green-800' },
}

const METHOD_LABELS: Record<string, string> = {
  transfer: '계좌이체',
  cash: '현금',
}

export default function Payments() {
  const [payments, setPayments] = useState<Payment[]>([])
  const [filter, setFilter] = useState<string>('pending')
  const [loading, setLoading] = useState(false)

  // 메시지 다이얼로그
  const [msgOpen, setMsgOpen] = useState(false)
  const [msgText, setMsgText] = useState('')
  const [copied, setCopied] = useState(false)

  // 입금 확인 다이얼로그
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [confirmId, setConfirmId] = useState<number | null>(null)
  const [confirmMethod, setConfirmMethod] = useState('transfer')
  const [confirmMemo, setConfirmMemo] = useState('')

  const fetchPayments = async () => {
    setLoading(true)
    const url = filter === 'all' ? '/api/payments' : `/api/payments?status=${filter}`
    const res = await fetch(url)
    setPayments(await res.json())
    setLoading(false)
  }

  useEffect(() => { fetchPayments() }, [filter])

  const formatAmount = (amount: number) => amount.toLocaleString() + '원'
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('ko-KR')
  }

  // 메시지 생성
  const handleMessage = async (paymentId: number) => {
    const res = await fetch(`/api/payments/${paymentId}/message`, { method: 'POST' })
    if (!res.ok) return
    const data = await res.json()
    setMsgText(data.message)
    setCopied(false)
    setMsgOpen(true)
    fetchPayments()
  }

  // 클립보드 복사
  const handleCopy = async () => {
    await navigator.clipboard.writeText(msgText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // 입금 확인 다이얼로그 열기
  const openConfirm = (paymentId: number) => {
    setConfirmId(paymentId)
    setConfirmMethod('transfer')
    setConfirmMemo('')
    setConfirmOpen(true)
  }

  // 입금 확인 처리
  const handleConfirm = async () => {
    if (!confirmId) return
    const res = await fetch(`/api/payments/${confirmId}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        payment_method: confirmMethod,
        memo: confirmMemo || null,
      }),
    })
    if (!res.ok) return
    setConfirmOpen(false)
    fetchPayments()
  }

  const pendingCount = payments.filter((p) => p.status === 'pending').length
  const totalPending = payments
    .filter((p) => p.status === 'pending')
    .reduce((sum, p) => sum + p.amount, 0)

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">수업료 관리</h2>
      </div>

      {/* 필터 + 요약 */}
      <div className="flex items-center gap-4 mb-4">
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="pending">미납</SelectItem>
            <SelectItem value="paid">납부완료</SelectItem>
            <SelectItem value="all">전체</SelectItem>
          </SelectContent>
        </Select>
        {filter === 'pending' && pendingCount > 0 && (
          <p className="text-sm text-muted-foreground">
            미납 {pendingCount}건 / 합계 {totalPending.toLocaleString()}원
          </p>
        )}
      </div>

      {/* 수업료 테이블 */}
      {loading ? (
        <p className="text-muted-foreground">로딩 중...</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>학생</TableHead>
              <TableHead>수업반</TableHead>
              <TableHead>회차</TableHead>
              <TableHead>수업료</TableHead>
              <TableHead>상태</TableHead>
              <TableHead>메시지</TableHead>
              <TableHead>납부일</TableHead>
              <TableHead className="text-right">관리</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {payments.map((p) => {
              const statusInfo = STATUS_LABELS[p.status] ?? { label: p.status, color: '' }
              return (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.student_name}</TableCell>
                  <TableCell>{p.class_group_name ?? '-'}</TableCell>
                  <TableCell>{p.cycle_number}회차</TableCell>
                  <TableCell>{formatAmount(p.amount)}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusInfo.color}`}>
                      {statusInfo.label}
                    </span>
                  </TableCell>
                  <TableCell>
                    {p.message_sent ? (
                      <Badge variant="secondary">발송완료</Badge>
                    ) : (
                      <span className="text-muted-foreground text-sm">미발송</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {p.paid_at ? formatDate(p.paid_at) : '-'}
                    {p.payment_method && (
                      <span className="text-muted-foreground text-xs ml-1">
                        ({METHOD_LABELS[p.payment_method] ?? p.payment_method})
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex gap-1 justify-end">
                      {p.status === 'pending' && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs"
                            onClick={() => handleMessage(p.id)}
                          >
                            메시지
                          </Button>
                          <Button
                            size="sm"
                            className="text-xs"
                            onClick={() => openConfirm(p.id)}
                          >
                            입금확인
                          </Button>
                        </>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )
            })}
            {payments.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-muted-foreground py-8">
                  {filter === 'pending' ? '미납 내역이 없습니다.' : '수업료 내역이 없습니다.'}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}

      {/* 메시지 다이얼로그 */}
      <Dialog open={msgOpen} onOpenChange={setMsgOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>학부모 안내 메시지</DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <pre className="whitespace-pre-wrap bg-muted p-4 rounded-md text-sm leading-relaxed">
              {msgText}
            </pre>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMsgOpen(false)}>닫기</Button>
            <Button onClick={handleCopy}>
              {copied ? '복사됨!' : '클립보드 복사'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 입금 확인 다이얼로그 */}
      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>입금 확인</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>결제 방법</Label>
              <Select value={confirmMethod} onValueChange={setConfirmMethod}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="transfer">계좌이체</SelectItem>
                  <SelectItem value="cash">현금</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              <Label>메모 (선택)</Label>
              <Input
                value={confirmMemo}
                onChange={(e) => setConfirmMemo(e.target.value)}
                placeholder="메모를 입력하세요"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirmOpen(false)}>취소</Button>
            <Button onClick={handleConfirm}>확인</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
