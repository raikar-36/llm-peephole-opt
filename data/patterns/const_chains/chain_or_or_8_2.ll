define i32 @chain_or_or_8_2(i32 %x) {
entry:
  %tmp = or i32 %x, 8
  %result = or i32 %tmp, 2
  ret i32 %result
}
