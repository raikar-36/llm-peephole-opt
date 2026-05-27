define i32 @chain_and_and_255_4(i32 %x) {
entry:
  %tmp = and i32 %x, 255
  %result = and i32 %tmp, 4
  ret i32 %result
}
