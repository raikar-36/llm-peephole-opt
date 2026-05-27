define i32 @chain_sub_add_8_8(i32 %x) {
entry:
  %tmp = sub i32 %x, 8
  %result = add i32 %tmp, 8
  ret i32 %result
}
