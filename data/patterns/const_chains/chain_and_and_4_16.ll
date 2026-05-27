define i32 @chain_and_and_4_16(i32 %x) {
entry:
  %tmp = and i32 %x, 4
  %result = and i32 %tmp, 16
  ret i32 %result
}
