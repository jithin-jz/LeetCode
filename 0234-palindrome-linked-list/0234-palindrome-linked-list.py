class Solution:
    def isPalindrome(self, head: Optional[ListNode]) -> bool:
        vals = []
        curr = head
        while curr:
            vals.append(curr.val)
            curr = curr.next
        
        start, end = 0, len(vals) - 1
        while start < end:
            if vals[start] != vals[end]:
                return False
            start += 1
            end -= 1
        return True