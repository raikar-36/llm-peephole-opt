define i32 @chain_or_or_2_1(i32 %x) {
entry:
  %tmp = or i32 %x, 2
  %result = or i32 %tmp, 1
  ret i32 %result
}
