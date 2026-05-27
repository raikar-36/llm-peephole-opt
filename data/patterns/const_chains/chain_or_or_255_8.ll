define i32 @chain_or_or_255_8(i32 %x) {
entry:
  %tmp = or i32 %x, 255
  %result = or i32 %tmp, 8
  ret i32 %result
}
