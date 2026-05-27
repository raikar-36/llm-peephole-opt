define i32 @chain_and_and_4_8(i32 %x) {
entry:
  %tmp = and i32 %x, 4
  %result = and i32 %tmp, 8
  ret i32 %result
}
