define i32 @chain_and_and_4_2(i32 %x) {
entry:
  %tmp = and i32 %x, 4
  %result = and i32 %tmp, 2
  ret i32 %result
}
